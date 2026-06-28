"""
Spark 批处理作业 — 从 MySQL 读取禅道数据，计算分析指标后写入 PostgreSQL

演示大数据批处理能力: Spark 3.5 + JDBC
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, sum, when, lit, round as spark_round

# 初始化 Spark
spark = SparkSession.builder \
    .appName("ZentaoBatchAnalytics") \
    .config("spark.sql.shuffle.partitions", "2") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# ============ 读取 MySQL 数据 ============
mysql_url = "jdbc:mysql://zentao-mysql:3306/zentao?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC"
mysql_props = {"user": "zentao", "password": "zentao123", "driver": "com.mysql.cj.jdbc.Driver"}

tasks_df = spark.read.jdbc(mysql_url, "zt_task", properties=mysql_props)
bugs_df = spark.read.jdbc(mysql_url, "zt_bug", properties=mysql_props)
projects_df = spark.read.jdbc(mysql_url, "zt_project", properties=mysql_props)

print(f"读取: 任务={tasks_df.count()}, Bug={bugs_df.count()}, 项目={projects_df.count()}")

# ============ 计算分析指标 ============

# 1. 项目健康度
task_stats = tasks_df.groupBy("project_id").agg(
    count("*").alias("task_total"),
    sum(when(col("status") == "done", 1).otherwise(0)).alias("task_done")
)

bug_stats = bugs_df.groupBy("project_id").agg(
    count("*").alias("bug_total"),
    sum(when(col("status") == "resolved", 1).otherwise(0)).alias("bug_resolved")
)

health_df = projects_df.select("id", "name") \
    .join(task_stats, projects_df.id == task_stats.project_id, "left") \
    .join(bug_stats, projects_df.id == bug_stats.project_id, "left") \
    .fillna(0) \
    .withColumn("completion_rate",
        spark_round(when(col("task_total") > 0, col("task_done") / col("task_total")).otherwise(0), 2)) \
    .withColumn("bug_resolve_rate",
        spark_round(when(col("bug_total") > 0, col("bug_resolved") / col("bug_total")).otherwise(0), 2)) \
    .withColumn("health_score",
        spark_round(col("completion_rate") * 40 + col("bug_resolve_rate") * 30 + lit(30), 1)) \
    .withColumn("risk_level",
        when(col("health_score") < 25, "critical")
        .when(col("health_score") < 50, "high")
        .when(col("health_score") < 75, "medium")
        .otherwise("low")) \
    .select("id", "name", "health_score", "risk_level", "task_total", "task_done",
            "completion_rate", "bug_total", "bug_resolved", "bug_resolve_rate")

print("=== 项目健康度 ===")
health_df.show(20, False)

# 2. Bug 严重度分布
severity_dist = bugs_df.withColumn("severity_label",
    when(col("severity") == 1, "fatal")
    .when(col("severity") == 2, "serious")
    .when(col("severity") == 3, "normal")
    .otherwise("minor")
).groupBy("severity_label").agg(count("*").alias("count")) \
 .orderBy("severity_label")

print("=== Bug 严重度分布 ===")
severity_dist.show()

# 3. 任务状态分布
task_status_dist = tasks_df.groupBy("status").agg(count("*").alias("count")).orderBy("status")
print("=== 任务状态分布 ===")
task_status_dist.show()

# ============ 写入 PostgreSQL ============
pg_url = "jdbc:postgresql://ai_platform_postgres:5432/ai_platform"
pg_props = {"user": "postgres", "password": "postgres", "driver": "org.postgresql.Driver"}

health_df.write.jdbc(pg_url, "spark_project_health", mode="overwrite", properties=pg_props)
severity_dist.write.jdbc(pg_url, "spark_bug_severity", mode="overwrite", properties=pg_props)
task_status_dist.write.jdbc(pg_url, "spark_task_status", mode="overwrite", properties=pg_props)

print("=" * 50)
print("Spark 批处理完成! 结果已写入 PostgreSQL")
print("=" * 50)

spark.stop()
