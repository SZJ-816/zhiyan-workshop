"""
Kafka Producer — 从禅道 MySQL 抽取真实数据推送到 Kafka

数据流: 禅道 MySQL → Kafka Topics
- zentao_tasks   : 任务全量 + 增量
- zentao_bugs    : Bug 全量 + 增量
- zentao_projects: 项目状态
- zentao_events  : 实时事件流

运行方式: python zentao_producer.py
"""
import json
import time
import logging
from datetime import datetime, date
from typing import Optional

import pymysql
from kafka import KafkaProducer
from kafka.errors import KafkaError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ============ 配置 ============
MYSQL_CONFIG = {
    "host": "zentao-mysql",
    "port": 3306,
    "user": "zentao",
    "password": "zentao123",
    "database": "zentao",
    "charset": "utf8mb4",
}

KAFKA_CONFIG = {
    "bootstrap_servers": ["kafka:29092"],
    "value_serializer": lambda v: json.dumps(v, ensure_ascii=False, default=str).encode("utf-8"),
    "key_serializer": lambda v: str(v).encode("utf-8") if v else None,
}

TOPICS = {
    "tasks": "zentao_tasks",
    "bugs": "zentao_bugs",
    "projects": "zentao_projects",
    "events": "zentao_events",
}


class ZentaoKafkaProducer:
    """禅道数据 → Kafka 管道"""

    def __init__(self):
        self.producer: Optional[KafkaProducer] = None
        self.connection: Optional[pymysql.Connection] = None
        self.last_task_id = 0
        self.last_bug_id = 0
        self.last_event_id = 0

    def connect_mysql(self):
        self.connection = pymysql.connect(**MYSQL_CONFIG)
        log.info("MySQL 连接成功")

    def connect_kafka(self):
        retries = 0
        while retries < 30:
            try:
                self.producer = KafkaProducer(**KAFKA_CONFIG)
                log.info("Kafka 连接成功")
                return
            except KafkaError:
                retries += 1
                log.warning(f"Kafka 连接失败，重试 {retries}/30...")
                time.sleep(5)
        raise RuntimeError("Kafka 连接失败")

    def publish_tasks(self, full_sync: bool = False):
        """发布任务数据"""
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)
        if full_sync:
            cursor.execute(
                """SELECT t.*, p.name as project_name, u.realname as assignee_name
                   FROM zt_task t
                   LEFT JOIN zt_project p ON t.project_id = p.id
                   LEFT JOIN zt_user u ON t.assigned_to = u.id
                   ORDER BY t.id"""
            )
        else:
            cursor.execute(
                """SELECT t.*, p.name as project_name, u.realname as assignee_name
                   FROM zt_task t
                   LEFT JOIN zt_project p ON t.project_id = p.id
                   LEFT JOIN zt_user u ON t.assigned_to = u.id
                   WHERE t.id > %s ORDER BY t.id""",
                (self.last_task_id,),
            )

        rows = cursor.fetchall()
        for row in rows:
            self.producer.send(TOPICS["tasks"], key=row["id"], value=row)
            self.last_task_id = max(self.last_task_id, row["id"])
        self.producer.flush()
        log.info(f"任务已发布: {len(rows)} 条 (last_id={self.last_task_id})")
        cursor.close()

    def publish_bugs(self, full_sync: bool = False):
        """发布 Bug 数据"""
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)
        if full_sync:
            cursor.execute(
                """SELECT b.*, p.name as project_name, u.realname as assignee_name
                   FROM zt_bug b
                   LEFT JOIN zt_project p ON b.project_id = p.id
                   LEFT JOIN zt_user u ON b.assigned_to = u.id
                   ORDER BY b.id"""
            )
        else:
            cursor.execute(
                """SELECT b.*, p.name as project_name, u.realname as assignee_name
                   FROM zt_bug b
                   LEFT JOIN zt_project p ON b.project_id = p.id
                   LEFT JOIN zt_user u ON b.assigned_to = u.id
                   WHERE b.id > %s ORDER BY b.id""",
                (self.last_bug_id,),
            )

        rows = cursor.fetchall()
        for row in rows:
            severity_map = {1: "fatal", 2: "serious", 3: "normal", 4: "minor"}
            row["severity_label"] = severity_map.get(row.get("severity", 3), "normal")
            self.producer.send(TOPICS["bugs"], key=row["id"], value=row)
            self.last_bug_id = max(self.last_bug_id, row["id"])
        self.producer.flush()
        log.info(f"Bug 已发布: {len(rows)} 条 (last_id={self.last_bug_id})")
        cursor.close()

    def publish_projects(self):
        """发布项目汇总"""
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)
        cursor.execute(
            """SELECT p.*,
                      (SELECT COUNT(*) FROM zt_task t WHERE t.project_id = p.id) as task_count,
                      (SELECT COUNT(*) FROM zt_task t WHERE t.project_id = p.id AND t.status='done') as done_count,
                      (SELECT COUNT(*) FROM zt_bug b WHERE b.project_id = p.id) as bug_count,
                      (SELECT COUNT(*) FROM zt_bug b WHERE b.project_id = p.id AND b.status='resolved') as resolved_count
               FROM zt_project p ORDER BY p.id"""
        )
        rows = cursor.fetchall()
        for row in rows:
            self.producer.send(TOPICS["projects"], key=row["id"], value=row)
        self.producer.flush()
        log.info(f"项目已发布: {len(rows)} 条")
        cursor.close()

    def run_sync_loop(self, interval: int = 30):
        """持续同步循环"""
        log.info("=== 禅道 Kafka 数据管道启动 ===")
        self.connect_mysql()
        self.connect_kafka()

        # 首次全量同步
        self.publish_tasks(full_sync=True)
        self.publish_bugs(full_sync=True)
        self.publish_projects()

        # 增量同步循环
        while True:
            time.sleep(interval)
            try:
                self.publish_tasks()
                self.publish_bugs()
                self.publish_projects()
            except Exception as e:
                log.error(f"同步异常: {e}")
                try:
                    self.connection.ping(reconnect=True)
                except Exception:
                    self.connect_mysql()


if __name__ == "__main__":
    producer = ZentaoKafkaProducer()
    producer.run_sync_loop()
