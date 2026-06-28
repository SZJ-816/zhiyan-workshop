"""
Spark 批处理 — 从 Kafka 消费禅道数据，聚合分析后写入 PostgreSQL

分析维度:
1. 项目健康度评分 (任务完成率 + Bug解决率 + 进度偏离)
2. 人员效能排名 (完成任务数 + 预估偏差 + Bug修复数)
3. 任务/Bug 趋势统计 (按周/月聚合)
4. 严重度分布分析

运行方式: spark-submit --master spark://spark-master:7077 zentao_batch.py
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    col, from_json, count, avg, sum as spark_sum,
    window, lit, when, datediff, current_date, max as spark_max,
    to_timestamp, expr
)
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, DoubleType, TimestampType
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

POSTGRES_CONFIG = {
    "url": "jdbc:postgresql://ai_platform_postgres:5432/ai_platform",
    "user": "postgres",
    "password": "postgres",
    "driver": "org.postgresql.Driver",
}

KAFKA_CONFIG = {
    "bootstrap.servers": "kafka:29092",
    "subscribe": "zentao_tasks,zentao_bugs,zentao_projects",
    "startingOffsets": "earliest",
    "failOnDataLoss": "false",
}


class ZentaoSparkBatch:
    """禅道数据 Spark 批处理"""

    def __init__(self):
        self.spark = (
            SparkSession.builder.appName("ZentaoBatchAnalytics")
            .config("spark.sql.shuffle.partitions", "4")
            .config("spark.sql.streaming.checkpointLocation", "/tmp/spark/checkpoint")
            .getOrCreate()
        )
        self.spark.sparkContext.setLogLevel("WARN")

    def init_postgres(self):
        """初始化 analytics 表"""
        ddl_statements = [
            """CREATE TABLE IF NOT EXISTS project_health (
                project_id INTEGER PRIMARY KEY,
                project_name VARCHAR(200),
                task_total INTEGER, task_done INTEGER, completion_rate DOUBLE PRECISION,
                bug_total INTEGER, bug_resolved INTEGER, bug_resolve_rate DOUBLE PRECISION,
                overdue_tasks INTEGER, health_score DOUBLE PRECISION,
                risk_level VARCHAR(20), updated_at TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS member_performance (
                user_id INTEGER PRIMARY KEY,
                realname VARCHAR(50),
                tasks_done INTEGER, tasks_total INTEGER,
                bugs_fixed INTEGER, bugs_assigned INTEGER,
                avg_estimate DOUBLE PRECISION, avg_consumed DOUBLE PRECISION,
                efficiency_score DOUBLE PRECISION, updated_at TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS bug_severity_stats (
                project_id INTEGER, severity VARCHAR(20),
                count INTEGER, resolved_count INTEGER,
                avg_resolve_hours DOUBLE PRECISION,
                PRIMARY KEY (project_id, severity)
            )""",
            """CREATE TABLE IF NOT EXISTS weekly_trends (
                week_start DATE, project_id INTEGER,
                tasks_created INTEGER, tasks_done INTEGER,
                bugs_found INTEGER, bugs_resolved INTEGER,
                PRIMARY KEY (week_start, project_id)
            )""",
            """CREATE TABLE IF NOT EXISTS prediction_training_data (
                id SERIAL PRIMARY KEY,
                feature_json JSONB,
                target_label VARCHAR(100),
                target_value DOUBLE PRECISION,
                created_at TIMESTAMP DEFAULT NOW()
            )""",
        ]

        for ddl in ddl_statements:
            try:
                self.spark._jsc.hadoopConfiguration()
                props = {
                    "user": POSTGRES_CONFIG["user"],
                    "password": POSTGRES_CONFIG["password"],
                    "driver": POSTGRES_CONFIG["driver"],
                }
                jdbc_df = self.spark.read.jdbc(
                    url=POSTGRES_CONFIG["url"], table="(SELECT 1 as test) t", properties=props
                )
                # Execute DDL via JDBC
                import psycopg2
                conn = psycopg2.connect(
                    host="ai_platform_postgres", port=5432,
                    database="ai_platform", user="postgres", password="postgres"
                )
                conn.autocommit = True
                cur = conn.cursor()
                cur.execute(ddl)
                cur.close()
                conn.close()
            except Exception as e:
                log.warning(f"DDL init warning: {e}")

    def read_mysql_as_df(self, table: str) -> DataFrame:
        """直接从 MySQL 读取全量数据"""
        return (
            self.spark.read.format("jdbc")
            .option("url", "jdbc:mysql://zentao-mysql:3306/zentao?useSSL=false&serverTimezone=UTC")
            .option("dbtable", f"(SELECT * FROM {table}) t")
            .option("user", "zentao")
            .option("password", "zentao123")
            .option("driver", "com.mysql.cj.jdbc.Driver")
            .load()
        )

    def compute_project_health(self) -> DataFrame:
        """计算项目健康度"""
        tasks_df = self.read_mysql_as_df("zt_task")
        bugs_df = self.read_mysql_as_df("zt_bug")
        projects_df = self.read_mysql_as_df("zt_project")

        # 任务统计
        task_stats = tasks_df.groupBy("project_id").agg(
            count("*").alias("task_total"),
            spark_sum(when(col("status") == "done", 1).otherwise(0)).alias("task_done"),
            spark_sum(when((col("status") != "done") & (col("start_date").isNotNull()), 1).otherwise(0)).alias("overdue_tasks"),
        )

        # Bug统计
        bug_stats = bugs_df.groupBy("project_id").agg(
            count("*").alias("bug_total"),
            spark_sum(when(col("status") == "resolved", 1).otherwise(0)).alias("bug_resolved"),
        )

        # 关联
        result = projects_df.alias("p").join(task_stats.alias("t"), "project_id", "left").join(
            bug_stats.alias("b"), "project_id", "left"
        ).select(
            col("p.id").alias("project_id"),
            col("p.name").alias("project_name"),
            col("t.task_total"), col("t.task_done"),
            col("b.bug_total"), col("b.bug_resolved"),
            col("t.overdue_tasks"),
        )

        # 健康分计算: 完成率*40 + Bug解决率*30 + (100-逾期率)*30
        result = result.withColumn(
            "completion_rate",
            when(col("task_total") > 0, col("task_done") / col("task_total")).otherwise(0.0)
        ).withColumn(
            "bug_resolve_rate",
            when(col("bug_total") > 0, col("bug_resolved") / col("bug_total")).otherwise(0.0)
        ).withColumn(
            "overdue_penalty",
            when(col("task_total") > 0, col("overdue_tasks") / col("task_total") * 100).otherwise(0.0)
        ).withColumn(
            "health_score",
            col("completion_rate") * 40 + col("bug_resolve_rate") * 30 + (100 - col("overdue_penalty")) * 0.3
        ).withColumn(
            "risk_level",
            when(col("health_score") >= 75, lit("low"))
            .when(col("health_score") >= 50, lit("medium"))
            .when(col("health_score") >= 25, lit("high"))
            .otherwise(lit("critical"))
        ).withColumn("updated_at", current_date())

        return result

    def compute_member_performance(self) -> DataFrame:
        """计算成员效能"""
        tasks_df = self.read_mysql_as_df("zt_task")
        bugs_df = self.read_mysql_as_df("zt_bug")
        users_df = self.read_mysql_as_df("zt_user")

        task_perf = tasks_df.groupBy("assigned_to").agg(
            count("*").alias("tasks_total"),
            spark_sum(when(col("status") == "done", 1).otherwise(0)).alias("tasks_done"),
            avg("estimate").alias("avg_estimate"),
            avg("consumed").alias("avg_consumed"),
        )

        bug_perf = bugs_df.groupBy("assigned_to").agg(
            count("*").alias("bugs_assigned"),
            spark_sum(when(col("status") == "resolved", 1).otherwise(0)).alias("bugs_fixed"),
        )

        result = users_df.alias("u").join(task_perf.alias("t"), col("u.id") == col("t.assigned_to"), "left").join(
            bug_perf.alias("b"), col("u.id") == col("b.assigned_to"), "left"
        ).select(
            col("u.id").alias("user_id"),
            col("u.realname"),
            col("t.tasks_total"), col("t.tasks_done"),
            col("b.bugs_fixed"), col("b.bugs_assigned"),
            col("t.avg_estimate"), col("t.avg_consumed"),
        ).withColumn(
            "efficiency_score",
            when(col("tasks_total") > 0, col("tasks_done") / col("tasks_total") * 60 +
             when(col("bugs_assigned") > 0, col("bugs_fixed") / col("bugs_assigned") * 40).otherwise(0)).otherwise(0)
        ).withColumn("updated_at", current_date())

        return result

    def compute_bug_severity(self) -> DataFrame:
        """Bug 严重度分布"""
        bugs_df = self.read_mysql_as_df("zt_bug")
        result = bugs_df.groupBy("project_id", "severity").agg(
            count("*").alias("count"),
            spark_sum(when(col("status") == "resolved", 1).otherwise(0)).alias("resolved_count"),
        )
        return result

    def compute_weekly_trends(self) -> DataFrame:
        """周趋势统计"""
        tasks_df = self.read_mysql_as_df("zt_task")
        bugs_df = self.read_mysql_as_df("zt_bug")

        # 任务周趋势
        task_weekly = tasks_df.withColumn("week_start", expr("date_sub(created_at, dayofweek(created_at)-1)")).groupBy(
            "week_start", "project_id"
        ).agg(
            count("*").alias("tasks_created"),
            spark_sum(when(col("status") == "done", 1).otherwise(0)).alias("tasks_done"),
        )

        # Bug周趋势
        bug_weekly = bugs_df.withColumn("week_start", expr("date_sub(created_at, dayofweek(created_at)-1)")).groupBy(
            "week_start", "project_id"
        ).agg(
            count("*").alias("bugs_found"),
            spark_sum(when(col("status") == "resolved", 1).otherwise(0)).alias("bugs_resolved"),
        )

        result = task_weekly.join(bug_weekly, ["week_start", "project_id"], "outer").na.fill(0)
        return result

    def prepare_training_data(self) -> DataFrame:
        """准备 AI 训练数据"""
        tasks_df = self.read_mysql_as_df("zt_task")
        bugs_df = self.read_mysql_as_df("zt_bug")

        # 任务特征: estimate, priority, project_id, assignee → actual_hours (consumed)
        task_features = tasks_df.filter(col("consumed").isNotNull()).select(
            col("id"), col("name"), col("estimate"), col("priority"),
            col("project_id"), col("assigned_to"),
            col("consumed").alias("target_value"),
            lit("task_duration").alias("target_label"),
        )

        # Bug 特征: title, project_id → severity
        bug_features = bugs_df.select(
            col("id"), col("title"), col("severity").cast("int").alias("target_value"),
            col("project_id"), col("assigned_to"),
            lit("bug_severity").alias("target_label"),
        )

        return task_features.unionByName(bug_features, allowMissingColumns=True)

    def write_to_postgres(self, df: DataFrame, table: str, mode: str = "overwrite"):
        """写入 PostgreSQL"""
        df.write.format("jdbc").options(
            url=POSTGRES_CONFIG["url"],
            dbtable=table,
            user=POSTGRES_CONFIG["user"],
            password=POSTGRES_CONFIG["password"],
            driver=POSTGRES_CONFIG["driver"],
        ).mode(mode).save()
        log.info(f"写入 {table}: OK")

    def run_batch(self):
        """执行全量批处理"""
        log.info("=== Spark 批处理启动 ===")

        # 初始化表结构
        self.init_postgres()

        # 1. 项目健康度
        log.info("计算项目健康度...")
        health_df = self.compute_project_health()
        self.write_to_postgres(health_df, "project_health")

        # 2. 成员效能
        log.info("计算成员效能...")
        perf_df = self.compute_member_performance()
        self.write_to_postgres(perf_df, "member_performance")

        # 3. Bug严重度
        log.info("分析 Bug 严重度分布...")
        sev_df = self.compute_bug_severity()
        self.write_to_postgres(sev_df, "bug_severity_stats")

        # 4. 周趋势
        log.info("计算周趋势...")
        trend_df = self.compute_weekly_trends()
        self.write_to_postgres(trend_df, "weekly_trends")

        # 5. AI训练数据
        log.info("准备 AI 训练数据...")
        training_df = self.prepare_training_data()
        self.write_to_postgres(training_df, "prediction_training_data", mode="append")

        log.info("=== 批处理完成 ===")
        self.spark.stop()


if __name__ == "__main__":
    batch = ZentaoSparkBatch()
    batch.run_batch()
