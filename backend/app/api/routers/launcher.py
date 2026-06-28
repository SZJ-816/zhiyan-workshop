"""启动器API - 服务管理、日志、资源监控"""
import os
import psutil
from datetime import datetime
from fastapi import APIRouter

router = APIRouter(prefix="/api/launcher", tags=["launcher"])

# Docker client (lazy init, works when socket mounted)
_docker_client = None

def _get_docker():
    global _docker_client
    if _docker_client is not None:
        return _docker_client
    try:
        import docker
        _docker_client = docker.from_env()
        _docker_client.ping()
    except Exception:
        _docker_client = False
    return _docker_client

# ===== 服务定义 =====
SERVICE_DEFS = [
    {"id": "nginx", "name": "Nginx", "desc": "Web服务器 · 反向代理", "port": 80, "tier": "接入层", "icon": "🌐", "container": "zentao-nginx"},
    {"id": "fastapi", "name": "FastAPI", "desc": "应用服务 · REST API", "port": 8000, "tier": "应用层", "icon": "⚡", "container": "zentao-fastapi"},
    {"id": "mysql", "name": "MySQL", "desc": "关系型数据库", "port": 3306, "tier": "存储层", "icon": "💾", "container": "zentao-mysql"},
    {"id": "postgres", "name": "PostgreSQL", "desc": "数据仓库 · 分析型数据库", "port": 5432, "tier": "存储层", "icon": "🐘", "container": "ai_platform_postgres"},
    {"id": "redis", "name": "Redis", "desc": "缓存服务 · 消息代理", "port": 6379, "tier": "存储层", "icon": "💎", "container": "ai_platform_redis"},
    {"id": "kafka", "name": "Apache Kafka", "desc": "消息队列 · 事件流", "port": 9092, "tier": "大数据层", "icon": "📨", "container": "ai_platform_kafka"},
    {"id": "zookeeper", "name": "ZooKeeper", "desc": "分布式协调 · Kafka依赖", "port": 2181, "tier": "大数据层", "icon": "🐾", "container": "ai_platform_zookeeper"},
    {"id": "spark_master", "name": "Spark Master", "desc": "批处理引擎 · 主节点", "port": 7077, "tier": "大数据层", "icon": "⚙️", "container": "ai_platform_spark_master"},
    {"id": "spark_worker", "name": "Spark Worker", "desc": "批处理引擎 · 工作节点", "port": 8081, "tier": "大数据层", "icon": "🔧", "container": "ai_platform_spark_worker"},
    {"id": "flink_jm", "name": "Flink JobManager", "desc": "流处理引擎 · 调度器", "port": 8083, "tier": "大数据层", "icon": "🌊", "container": "ai_platform_flink_jobmanager"},
    {"id": "flink_tm", "name": "Flink TaskManager", "desc": "流处理引擎 · 执行器", "port": None, "tier": "大数据层", "icon": "💧", "container": "ai_platform_flink_taskmanager"},
    {"id": "ai_model", "name": "AI模型服务", "desc": "Scikit-learn · 预测推理", "port": None, "tier": "AI层", "icon": "🧠", "container": "zentao-fastapi"},
]

def _get_container_status(container_name: str) -> dict:
    """获取Docker容器状态 (通过docker-py)"""
    try:
        client = _get_docker()
        if not client:
            return {"status": "unknown", "uptime": "-", "cpu": "-", "mem": "-"}

        container = client.containers.get(container_name)
        status = container.status

        if status == "running":
            attrs = container.attrs
            started = attrs.get("State", {}).get("StartedAt", "")[:19].replace("T", " ")

            # Get CPU/Mem from stats (non-streaming)
            try:
                stats = container.stats(stream=False)
                cpu_delta = stats.get("cpu_stats", {}).get("cpu_usage", {}).get("total_usage", 0) - \
                           stats.get("precpu_stats", {}).get("cpu_usage", {}).get("total_usage", 0)
                system_delta = stats.get("cpu_stats", {}).get("system_cpu_usage", 0) - \
                              stats.get("precpu_stats", {}).get("system_cpu_usage", 0)
                cpu_percent = round((cpu_delta / system_delta) * 100, 1) if system_delta > 0 else 0
                mem_usage = stats.get("memory_stats", {}).get("usage", 0)
                mem_limit = stats.get("memory_stats", {}).get("limit", 1)
                mem_percent = round((mem_usage / mem_limit) * 100, 1)
                mem_str = f"{mem_usage / (1024**2):.0f}MB"
            except Exception:
                cpu_percent = 0
                mem_str = "-"

            return {
                "status": "running",
                "uptime": started,
                "cpu": f"{cpu_percent}%",
                "mem": mem_str
            }
        elif status == "exited":
            return {"status": "stopped", "uptime": "-", "cpu": "-", "mem": "-"}
        else:
            return {"status": "unknown", "uptime": "-", "cpu": "-", "mem": "-"}
    except Exception:
        return {"status": "unknown", "uptime": "-", "cpu": "-", "mem": "-"}


@router.get("/services")
def list_services():
    """获取所有服务状态"""
    result = []
    for svc in SERVICE_DEFS:
        status_info = _get_container_status(svc["container"])
        result.append({**svc, **status_info})
    return result


@router.post("/services/{service_id}/{action}")
def control_service(service_id: str, action: str):
    """控制单个服务 (start/stop/restart)"""
    svc = next((s for s in SERVICE_DEFS if s["id"] == service_id), None)
    if not svc:
        return {"success": False, "error": "服务不存在"}

    valid_actions = {"start", "stop", "restart"}
    if action not in valid_actions:
        return {"success": False, "error": f"无效操作: {action}"}

    try:
        client = _get_docker()
        if not client:
            return {"success": False, "error": "Docker未连接，请检查socket挂载"}

        container = client.containers.get(svc["container"])
        getattr(container, action)()

        return {"success": True, "action": action, "service": svc["name"]}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/resources")
def get_resources():
    """获取服务器资源使用"""
    try:
        cpu = psutil.cpu_percent(interval=0.3)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        return {
            "cpu_percent": round(cpu, 1),
            "mem_percent": round(mem.percent, 1),
            "mem_used_gb": round(mem.used / (1024**3), 2),
            "mem_total": f"{mem.total / (1024**3):.1f} GB",
            "disk_percent": round(disk.percent, 1),
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_total_gb": round(disk.total / (1024**3), 2),
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/logs")
def get_logs(lines: int = 80):
    """获取FastAPI容器日志"""
    log_lines = []
    try:
        client = _get_docker()
        if client:
            container = client.containers.get("zentao-fastapi")
            log_output = container.logs(tail=lines).decode("utf-8", errors="replace")
            for line in log_output.strip().split("\n")[-lines:]:
                level = "ok"
                if "ERROR" in line or "error" in line.lower():
                    level = "err"
                elif "WARNING" in line or "warn" in line.lower():
                    level = "warn"
                log_lines.append({
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "level": level,
                    "msg": line[:300]
                })

        if not log_lines:
            log_lines = [{
                "time": datetime.now().strftime("%H:%M:%S"),
                "level": "ok",
                "msg": "WorkNest Launcher 就绪 · 共 " + str(len(SERVICE_DEFS)) + " 个服务实例"
            }]
    except Exception as e:
        log_lines = [{
            "time": datetime.now().strftime("%H:%M:%S"),
            "level": "err",
            "msg": f"日志获取失败: {str(e)}"
        }]

    return {"logs": log_lines}
