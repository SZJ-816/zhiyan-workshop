"""禅道项目管理系统 - FastAPI主应用"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import init_db, SessionLocal
from app.api.routers import (
    auth, dashboard, products, projects, bugs, users, launcher,
    ai_prediction, ai_chat, innovation, data_assets, transformation
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时：初始化数据库
    init_db()
    yield

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(products.router)
app.include_router(projects.router)
app.include_router(bugs.router)
app.include_router(users.router)
app.include_router(launcher.router)
app.include_router(ai_prediction.router)
app.include_router(ai_chat.router)
app.include_router(innovation.router)
app.include_router(data_assets.router)
app.include_router(transformation.router)

@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}

# ===== 数据初始化API =====
@app.post("/api/init/seed")
def seed_database():
    """最小化初始化 — 仅创建部门和超级管理员，团队自行录入真实数据"""
    from app.models.models import Department, User
    from passlib.context import CryptContext
    from datetime import datetime
    from sqlalchemy import text

    pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
    db = SessionLocal()

    try:
        # 清空所有表
        for tbl_name in ["zt_activity", "zt_bug", "zt_task", "zt_story",
                         "zt_project", "zt_product", "zt_user", "zt_department"]:
            db.execute(text(f"DELETE FROM {tbl_name}"))
        db.commit()
        # 重置自增计数
        for tbl_name in ["zt_activity", "zt_bug", "zt_task", "zt_story",
                         "zt_project", "zt_product", "zt_user", "zt_department"]:
            db.execute(text(f"ALTER TABLE {tbl_name} AUTO_INCREMENT = 1"))
        db.commit()

        # 创建 5 个部门（组织架构）
        depts = [
            Department(name="技术研发部",  sort=1),
            Department(name="产品管理部",  sort=2),
            Department(name="质量保障部",  sort=3),
            Department(name="运营管理部",  sort=4),
            Department(name="UED设计部",   sort=5),
        ]
        db.add_all(depts)
        db.flush()

        # 仅创建超级管理员（其余用户请在前端自行添加）
        admin = User(
            account="admin", realname="管理员", role="admin",
            department_id=1, avatar_color="#6366f1", email="admin@system.local",
            password=pwd.hash("123456"),
            created_at=datetime.now()
        )
        db.add(admin)
        db.commit()

        return {
            "success": True,
            "message": "系统初始化完成 — 已就绪，请开始录入真实项目数据",
            "stats": {"users": 1, "departments": 5}
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        db.close()
