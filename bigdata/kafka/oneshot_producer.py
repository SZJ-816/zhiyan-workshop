"""
Kafka One-Shot Producer — 一次性将禅道数据推送到 Kafka (confluent-kafka 版本)
"""
import json
import time
import logging
import sys

import pymysql
from confluent_kafka import Producer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# 配置
KAFKA_BROKER = "kafka:29092"
MYSQL_CONFIG = {
    "host": "zentao-mysql", "port": 3306,
    "user": "zentao", "password": "zentao123",
    "database": "zentao", "charset": "utf8mb4",
}

TOPICS = {
    "tasks": "zentao_tasks", "bugs": "zentao_bugs",
    "projects": "zentao_projects", "events": "zentao_events",
}


def delivery_callback(err, msg):
    if err:
        log.error(f"发送失败: {err}")
    else:
        log.debug(f"已发送到 {msg.topic()} [{msg.partition()}]")


def create_producer():
    conf = {"bootstrap.servers": KAFKA_BROKER}
    for i in range(30):
        try:
            p = Producer(conf)
            p.list_topics(timeout=5)
            log.info("Kafka 连接成功")
            return p
        except Exception as e:
            log.warning(f"Kafka 连接失败 ({i+1}/30): {e}")
            time.sleep(3)
    raise RuntimeError("Kafka 无法连接")


def main():
    log.info("=== 禅道 → Kafka 数据推送 ===")

    conn = pymysql.connect(**MYSQL_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    producer = create_producer()

    total = 0

    # 1. 任务
    cursor.execute("""
        SELECT t.*, p.name as project_name, u.realname as assignee_name
        FROM zt_task t LEFT JOIN zt_project p ON t.project_id=p.id
        LEFT JOIN zt_user u ON t.assigned_to=u.id ORDER BY t.id
    """)
    for row in cursor.fetchall():
        producer.produce(
            TOPICS["tasks"],
            key=str(row["id"]),
            value=json.dumps(row, ensure_ascii=False, default=str),
            callback=delivery_callback,
        )
    producer.flush()
    log.info(f"任务: {cursor.rowcount} 条")
    total += cursor.rowcount

    # 2. Bug
    cursor.execute("""
        SELECT b.*, p.name as project_name, u.realname as assignee_name
        FROM zt_bug b LEFT JOIN zt_project p ON b.project_id=p.id
        LEFT JOIN zt_user u ON b.assigned_to=u.id ORDER BY b.id
    """)
    smap = {1: "fatal", 2: "serious", 3: "normal", 4: "minor"}
    for row in cursor.fetchall():
        row["severity_label"] = smap.get(row.get("severity", 3), "normal")
        producer.produce(
            TOPICS["bugs"],
            key=str(row["id"]),
            value=json.dumps(row, ensure_ascii=False, default=str),
        )
    producer.flush()
    log.info(f"Bug: {cursor.rowcount} 条")
    total += cursor.rowcount

    # 3. 项目
    cursor.execute("""
        SELECT p.*,
          (SELECT COUNT(*) FROM zt_task t WHERE t.project_id=p.id) as task_count,
          (SELECT COUNT(*) FROM zt_task t WHERE t.project_id=p.id AND t.status='done') as done_count,
          (SELECT COUNT(*) FROM zt_bug b WHERE b.project_id=p.id) as bug_count,
          (SELECT COUNT(*) FROM zt_bug b WHERE b.project_id=p.id AND b.status='resolved') as resolved_count
        FROM zt_project p ORDER BY p.id
    """)
    for row in cursor.fetchall():
        producer.produce(
            TOPICS["projects"],
            key=str(row["id"]),
            value=json.dumps(row, ensure_ascii=False, default=str),
        )
    producer.flush()
    log.info(f"项目: {cursor.rowcount} 条")
    total += cursor.rowcount

    # 4. 事件
    cursor.execute("""
        SELECT 'task' as event_type, id as entity_id,
               CONCAT('Task #', id, ': ', name) as title,
               status, created_at
        FROM zt_task ORDER BY created_at DESC LIMIT 50
    """)
    for row in cursor.fetchall():
        producer.produce(
            TOPICS["events"],
            key=f"task_{row['entity_id']}",
            value=json.dumps(row, ensure_ascii=False, default=str),
        )
    producer.flush()
    log.info(f"事件: {cursor.rowcount} 条")
    total += cursor.rowcount

    producer.flush()
    cursor.close()
    conn.close()
    log.info(f"=== 推送完成: 共 {total} 条 ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
