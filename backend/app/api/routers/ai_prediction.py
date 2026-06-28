"""AI预测 API路由 — 基于禅道系统真实数据"""
import socket
import json as _json
from datetime import datetime
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from ai_model.inference.zentao_predictor import predictor

router = APIRouter(prefix="/api/ai", tags=["AI预测"])


# ==================== Pydantic 请求模型 ====================

class BugSeverityRequest(BaseModel):
    title: str = Field(..., min_length=1, description="Bug 标题", examples=["登录页面点击按钮后白屏3秒"])


class TaskDurationRequest(BaseModel):
    estimate: float = Field(default=16.0, ge=0.5, description="预估工时(小时)")
    priority: str = Field(default="medium", description="优先级: urgent/high/medium/low")
    project_id: int = Field(default=1, ge=1, description="项目ID")
    assigned_to: int = Field(default=1, ge=1, description="负责人ID")


class TrainRequest(BaseModel):
    model: str = Field(default="all", description="模型类型: all/bug_severity/task_duration/project_risk")


# ==================== 模型信息 ====================

@router.get("/model-info")
def get_model_info():
    """获取AI模型信息"""
    return {
        "current_model": predictor.current_model,
        "models_loaded": list(predictor.models.keys()),
        "training_count": predictor.training_count,
        "prediction_count": predictor.prediction_count,
        "available_models": ["bug_severity", "task_duration", "project_risk"],
    }


# ==================== Bug 严重度预测 ====================

@router.post("/predict/bug-severity")
async def predict_bug_severity(req: BugSeverityRequest):
    """预测 Bug 严重度

    POST /api/ai/predict/bug-severity
    Body: {"title": "登录页面点击按钮后白屏3秒"}
    """
    result = predictor.predict_bug_severity(req.title)
    return {"success": True, "data": result}


# ==================== 任务耗时预测 ====================

@router.post("/predict/task-duration")
async def predict_task_duration(req: TaskDurationRequest):
    """预测任务完成耗时

    POST /api/ai/predict/task-duration
    Body: {"estimate": 16, "priority": "high", "project_id": 1, "assigned_to": 1}
    """
    result = predictor.predict_task_duration(
        req.estimate, req.priority, req.project_id, req.assigned_to
    )
    return {"success": True, "data": result}


# ==================== 项目风险预测 ====================

@router.get("/predict/project-risk/{project_id}")
def predict_project_risk(project_id: int):
    """预测项目风险

    GET /api/ai/predict/project-risk/1
    """
    result = predictor.predict_project_risk(project_id)
    return {"success": True, "data": result}


# ==================== 趋势预测 & 数据洞察 ====================

@router.get("/insights")
def get_data_insights():
    """获取系统数据洞察 (替代原有的假趋势预测)

    GET /api/ai/insights
    """
    insights = predictor.get_data_insights()
    return {"success": True, "data": insights}


# ==================== 训练触发 ====================

@router.post("/train")
async def trigger_training(req: TrainRequest = TrainRequest()):
    """触发模型训练

    POST /api/ai/train
    Body: {"model": "all"}  # 可选: bug_severity, task_duration, project_risk
    """
    from ai_model.training.train_zentao_model import ZentaoAITrainer

    model_type = req.model
    trainer = ZentaoAITrainer()

    if model_type == "all":
        result = trainer.train_all()
    elif model_type == "bug_severity":
        bugs = trainer.fetch_bugs()
        trainer.train_bug_severity_model(bugs)
        result = {"models": {"bug_severity": {"samples": len(bugs)}}}
    elif model_type == "task_duration":
        tasks = trainer.fetch_tasks()
        trainer.train_task_duration_model(tasks)
        result = {"models": {"task_duration": {"samples": len(tasks)}}}
    elif model_type == "project_risk":
        projects = trainer.fetch_projects()
        trainer.train_project_risk_model(projects)
        result = {"models": {"project_risk": {"samples": len(projects)}}}
    else:
        return {"success": False, "error": f"未知模型类型: {model_type}"}

    # 重新加载模型
    predictor._load_models()
    predictor.training_count += 1

    return {"success": True, "data": result}


# ==================== 管道状态检测 (真实探测) ====================

def _tcp_probe(host: str, port: int, timeout: float = 2.0) -> bool:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        result = s.connect_ex((host, port))
        s.close()
        return result == 0
    except Exception:
        return False


def _check_kafka() -> dict:
    kafka_alive = _tcp_probe("kafka", 9092, timeout=2.0)
    status = "online" if kafka_alive else "offline"
    topics = []
    if kafka_alive:
        try:
            from confluent_kafka.admin import AdminClient
            admin = AdminClient({"bootstrap.servers": "kafka:9092"})
            meta = admin.list_topics(timeout=3)
            topics = list(meta.topics.keys())
        except Exception:
            pass
    return {
        "name": "Kafka 消息队列", "status": status,
        "detail": f"{len(topics)} topics" if topics else ("服务可达" if kafka_alive else "无法连接"),
        "topics": topics, "port_9092": kafka_alive,
    }


def _check_spark() -> dict:
    master_alive = _tcp_probe("spark-master", 7077, timeout=2.0)
    webui = _tcp_probe("spark-master", 8080, timeout=2.0)
    return {
        "name": "Spark 批处理",
        "status": "online" if master_alive else "offline",
        "detail": "Master可达" if master_alive else "无法连接",
        "master_7077": master_alive, "webui_8080": webui,
    }


def _check_flink() -> dict:
    jm_alive = _tcp_probe("flink-jobmanager", 6123, timeout=2.0)
    webui = _tcp_probe("flink-jobmanager", 8081, timeout=2.0)
    return {
        "name": "Flink 流计算",
        "status": "online" if jm_alive else "offline",
        "detail": "JobManager可达" if jm_alive else "无法连接",
        "rpc_6123": jm_alive, "webui_8081": webui,
    }


def _check_model() -> dict:
    return {
        "name": "AI 模型", "status": "online",
        "detail": f"{predictor.current_model} | 预测{predictor.prediction_count}次",
        "models": list(predictor.models.keys()),
    }


def _check_mysql() -> dict:
    from sqlalchemy import text
    from app.core.database import SessionLocal
    try:
        db = SessionLocal()
        tables = {}
        for tbl in ["zt_user", "zt_product", "zt_project", "zt_task", "zt_bug"]:
            try:
                result = db.execute(text(f"SELECT COUNT(*) FROM {tbl}"))
                tables[tbl] = result.scalar() or 0
            except Exception:
                tables[tbl] = 0
        db.close()
        return {"status": "online", "detail": f"{tables['zt_user']}用户/{tables['zt_project']}项目/{tables['zt_task']}任务/{tables['zt_bug']}Bug", "tables": tables}
    except Exception:
        return {"status": "offline", "detail": "连接失败", "tables": {}}


def _check_postgres() -> dict:
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="postgres", port=5432, database="ai_platform",
            user="postgres", password="postgres", connect_timeout=3
        )
        cur = conn.cursor()
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        pg_tables = [r[0] for r in cur.fetchall()]
        cur.close(); conn.close()
        return {"status": "online", "detail": f"{len(pg_tables)}张分析表", "tables": pg_tables}
    except Exception:
        return {"status": "offline", "detail": "连接失败", "tables": []}


@router.get("/pipeline-status")
def get_pipeline_status():
    kafka = _check_kafka()
    spark = _check_spark()
    flink = _check_flink()
    model = _check_model()
    mysql = _check_mysql()
    postgres = _check_postgres()

    return {
        "success": True,
        "timestamp": datetime.now().isoformat(),
        "services": {
            "kafka": kafka, "spark": spark, "flink": flink,
            "model": model, "mysql": mysql, "postgres": postgres,
        },
        "pipes": [
            {
                "id": 1, "name": "实时数据摄取",
                "desc": "禅道 MySQL → Apache Kafka",
                "nodes": ["MySQL", "Kafka"],
                "status": kafka["status"],
                "detail": f"MySQL: {mysql['detail']} | {kafka['detail']}",
            },
            {
                "id": 2, "name": "批处理分析",
                "desc": "Kafka → Apache Spark → PostgreSQL",
                "nodes": ["Kafka", "Spark", "PostgreSQL"],
                "status": spark["status"],
                "detail": f"{spark['detail']} | PG: {postgres['detail']}",
            },
            {
                "id": 3, "name": "实时流计算",
                "desc": "Kafka → Apache Flink → 实时指标",
                "nodes": ["Kafka", "Flink"],
                "status": flink["status"],
                "detail": flink["detail"],
            },
            {
                "id": 4, "name": "AI 推理管道",
                "desc": "训练数据 → ML模型 → 预测API",
                "nodes": ["训练数据", "ML模型", "预测API"],
                "status": model["status"],
                "detail": model["detail"],
            },
        ],
    }
