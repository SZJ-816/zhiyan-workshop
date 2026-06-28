"""
Kafka Consumer — 实时消费禅道数据流，写入 PostgreSQL 分析库
演示数据管道: Kafka → Consumer → PostgreSQL
"""
import json
import time
import logging
from datetime import datetime

import pymysql
import psycopg2
from kafka import KafkaConsumer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

PG_CONFIG = {
    "host": "ai_platform_postgres",
    "port": 5432,
    "user": "postgres",
    "password": "postgres",
    "database": "ai_platform",
}

KAFKA_CONFIG = {
    "bootstrap_servers": ["kafka:29092"],
    "group_id": "zentao_analytics",
    "value_deserializer": lambda v: json.loads(v.decode("utf-8")),
    "auto_offset_reset": "earliest",
}


def setup_postgres():
    """创建分析表"""
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS analysis_task_hourly (
            id SERIAL PRIMARY KEY,
            hour TIMESTAMP NOT NULL,
            total_count INT DEFAULT 0,
            done_count INT DEFAULT 0,
            high_priority_count INT DEFAULT 0,
            project_id INT,
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS analysis_bug_hourly (
            id SERIAL PRIMARY KEY,
            hour TIMESTAMP NOT NULL,
            total_count INT DEFAULT 0,
            resolved_count INT DEFAULT 0,
            serious_count INT DEFAULT 0,
            project_id INT,
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    cur.close()
    conn.close()
    log.info("PostgreSQL 分析表已创建")


def process_task(msg, pg_conn):
    """处理任务消息"""
    task = msg.value
    hour = datetime.now().replace(minute=0, second=0, microsecond=0)
    project_id = task.get("project_id", 0)

    cur = pg_conn.cursor()
    cur.execute("""
        INSERT INTO analysis_task_hourly (hour, total_count, done_count, high_priority_count, project_id)
        VALUES (%s, 1, %s, %s, %s)
        ON CONFLICT DO NOTHING
    """, (
        hour,
        1 if task.get("status") == "done" else 0,
        1 if task.get("priority") and str(task["priority"]) in ("1", "2", "urgent", "high") else 0,
        project_id,
    ))
    pg_conn.commit()
    cur.close()


def process_bug(msg, pg_conn):
    """处理 Bug 消息"""
    bug = msg.value
    hour = datetime.now().replace(minute=0, second=0, microsecond=0)
    project_id = bug.get("project_id", 0)
    severity = bug.get("severity", 3)

    cur = pg_conn.cursor()
    cur.execute("""
        INSERT INTO analysis_bug_hourly (hour, total_count, resolved_count, serious_count, project_id)
        VALUES (%s, 1, %s, %s, %s)
        ON CONFLICT DO NOTHING
    """, (
        hour,
        1 if bug.get("status") == "resolved" else 0,
        1 if int(severity) <= 2 else 0,
        project_id,
    ))
    pg_conn.commit()
    cur.close()


def main():
    log.info("=== 禅道数据实时消费管道启动 ===")

    # 初始化 PostgreSQL
    setup_postgres()
    pg_conn = psycopg2.connect(**PG_CONFIG)

    # 创建消费者
    consumer = KafkaConsumer(
        "zentao_tasks", "zentao_bugs",
        **KAFKA_CONFIG
    )

    log.info("Kafka 消费者已启动，等待数据...")
    count = {"tasks": 0, "bugs": 0}

    try:
        for msg in consumer:
            if msg.topic == "zentao_tasks":
                process_task(msg, pg_conn)
                count["tasks"] += 1
            elif msg.topic == "zentao_bugs":
                process_bug(msg, pg_conn)
                count["bugs"] += 1

            total = count["tasks"] + count["bugs"]
            if total % 10 == 0:
                log.info(f"已处理: 任务={count['tasks']}, Bug={count['bugs']}")

            # 一次性消费模式 - 1分钟后退出
            if total > 0 and time.time() - consumer._last_poll > 30:
                log.info("30秒内无新消息，管道空闲中...")

    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()
        pg_conn.close()
        log.info(f"管道关闭. 共处理: 任务={count['tasks']}, Bug={count['bugs']}")


if __name__ == "__main__":
    main()
