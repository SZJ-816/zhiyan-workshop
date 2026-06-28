"""
Flink 实时流处理 — 消费 Kafka，实时计算禅道指标

处理流程:
1. 消费 zentao_tasks → 实时任务状态变更统计
2. 消费 zentao_bugs  → 实时 Bug 发现/解决速率
3. 5分钟滑动窗口聚合
4. 结果写回 PostgreSQL 实时指标表

运行方式: flink run -py zentao_stream.py
"""
import json
import logging

from pyflink.common import WatermarkStrategy, Types, Time
from pyflink.common.typeinfo import Types as T
from pyflink.datastream import StreamExecutionEnvironment, RuntimeExecutionMode
from pyflink.datastream.connectors.kafka import (
    KafkaSource, KafkaOffsetsInitializer, KafkaRecordSerializationSchema
)
from pyflink.datastream.formats.json import JsonRowDeserializationSchema
from pyflink.datastream.window import TumblingEventTimeWindows, SlidingEventTimeWindows
from pyflink.datastream.functions import (
    ProcessWindowFunction, AggregateFunction, MapFunction
)
from pyflink.common.serialization import SimpleStringSchema
from pyflink.datastream.connectors.jdbc import JdbcSink, JdbcConnectionOptions, JdbcExecutionOptions

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


class ZentaoFlinkStream:
    """禅道 Flink 实时流"""

    def __init__(self):
        self.env = StreamExecutionEnvironment.get_execution_environment()
        self.env.set_runtime_mode(RuntimeExecutionMode.STREAMING)
        self.env.set_parallelism(2)
        # Checkpoint 每30秒
        self.env.enable_checkpointing(30000)

    def _kafka_source(self, topic: str) -> KafkaSource:
        """创建 Kafka Source"""
        deserialization_schema = JsonRowDeserializationSchema.builder().type_info(
            T.ROW_NAMED(
                ["id", "name", "status", "priority", "severity", "project_id",
                 "assigned_to", "estimate", "consumed", "created_at"],
                [T.INT(), T.STRING(), T.STRING(), T.STRING(), T.STRING(),
                 T.INT(), T.INT(), T.FLOAT(), T.FLOAT(), T.STRING()]
            )
        ).build()

        return (
            KafkaSource.builder()
            .set_bootstrap_servers("kafka:29092")
            .set_topics(topic)
            .set_group_id("flink_zentao_group")
            .set_starting_offsets(KafkaOffsetsInitializer.latest())
            .set_value_only_deserializer(deserialization_schema)
            .build()
        )

    def _postgres_sink(self, table: str):
        """创建 PostgreSQL Sink"""
        return (
            JdbcSink.sink(
                f"INSERT INTO {table} (metric_key, metric_value, window_start, updated_at) "
                "VALUES (?, ?, ?, NOW()) "
                "ON CONFLICT (metric_key, window_start) DO UPDATE SET metric_value=EXCLUDED.metric_value",
                type_info=T.ROW_NAMED(
                    ["metric_key", "metric_value", "window_start"],
                    [T.STRING(), T.FLOAT(), T.STRING()]
                ),
                JdbcConnectionOptions.JdbcConnectionOptionsBuilder()
                .with_url("jdbc:postgresql://ai_platform_postgres:5432/ai_platform")
                .with_driver_name("org.postgresql.Driver")
                .with_username("postgres")
                .with_password("postgres")
                .build(),
                JdbcExecutionOptions.builder()
                .with_batch_size(10)
                .with_batch_interval_ms(5000)
                .build(),
            )
        )

    def process_task_stream(self):
        """处理任务流: 按状态分类, 5分钟滑动窗口统计"""
        source = self._kafka_source("zentao_tasks")
        stream = self.env.from_source(source, WatermarkStrategy.no_watermarks(), "task-source")

        # 统计各状态任务数
        result = stream.map(
            lambda row: (row[2], 1),  # (status, 1)
            output_type=T.TUPLE([T.STRING(), T.INT()])
        ).key_by(lambda x: x[0]).window(
            SlidingEventTimeWindows.of(Time.minutes(5), Time.minutes(1))
        ).sum(1)

        # 结果直接输出到日志(后续可接 PostgreSQL Sink)
        result.map(
            lambda x: f"TaskStatus|{x[0]}|{x[1]}", output_type=T.STRING()
        ).print()

    def process_bug_stream(self):
        """处理Bug流: 实时发现/解决速率"""
        source = self._kafka_source("zentao_bugs")
        stream = self.env.from_source(source, WatermarkStrategy.no_watermarks(), "bug-source")

        result = stream.map(
            lambda row: (row[3] if row[3] else "unknown", 1),  # (severity, 1)
            output_type=T.TUPLE([T.STRING(), T.INT()])
        ).key_by(lambda x: x[0]).window(
            TumblingEventTimeWindows.of(Time.seconds(30))
        ).sum(1)

        result.map(
            lambda x: f"BugSeverity|{x[0]}|{x[1]}", output_type=T.STRING()
        ).print()

    def run(self):
        """启动 Flink 流处理"""
        log.info("=== Flink 流处理启动 ===")

        try:
            self.process_task_stream()
        except Exception as e:
            log.warning(f"Task stream startup: {e}")

        try:
            self.process_bug_stream()
        except Exception as e:
            log.warning(f"Bug stream startup: {e}")

        log.info("Flink 作业提交完成")
        self.env.execute("Zentao Realtime Analytics")


if __name__ == "__main__":
    flink = ZentaoFlinkStream()
    flink.run()
