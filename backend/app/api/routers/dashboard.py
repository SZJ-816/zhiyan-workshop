"""仪表盘API - 提供所有统计数据"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta, date
from app.core.database import get_db
from app.models.models import User, Project, Task, Bug, Story, Product, Activity
from app.schemas.schemas import DashboardStats
from .auth import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["仪表盘"])

@router.get("/stats")
def get_dashboard_stats(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    now = datetime.now()

    # 基础统计
    total_projects = db.query(func.count(Project.id)).scalar() or 0
    total_tasks = db.query(func.count(Task.id)).scalar() or 0
    active_tasks = db.query(func.count(Task.id)).filter(Task.status == "doing").scalar() or 0
    completed_tasks = db.query(func.count(Task.id)).filter(Task.status == "done").scalar() or 0
    total_bugs = db.query(func.count(Bug.id)).scalar() or 0
    active_bugs = db.query(func.count(Bug.id)).filter(Bug.status == "active").scalar() or 0
    resolved_bugs = db.query(func.count(Bug.id)).filter(Bug.status == "resolved").scalar() or 0
    total_stories = db.query(func.count(Story.id)).scalar() or 0
    active_stories = db.query(func.count(Story.id)).filter(
        Story.status.in_(["active", "developing", "testing"])
    ).scalar() or 0
    total_users = db.query(func.count(User.id)).scalar() or 0

    # 用户任务统计
    task_by_user = db.query(
        User.realname, func.count(Task.id).label("cnt")
    ).outerjoin(Task, Task.assigned_to == User.id).group_by(User.id).all()
    task_distribution = {name or "未分配": cnt for name, cnt in task_by_user}

    # Bug严重程度分布
    bug_by_severity = db.query(
        Bug.severity, func.count(Bug.id)
    ).filter(Bug.status != "closed").group_by(Bug.severity).all()
    sev_map = {"fatal": "致命", "serious": "严重", "normal": "一般", "minor": "轻微", "suggestion": "建议"}
    bug_severity = {sev_map.get(s, s): c for s, c in bug_by_severity}

    # 项目进度
    projects = db.query(Project).filter(Project.status != "closed").all()
    project_progress = []
    for p in projects:
        total = db.query(func.count(Task.id)).filter(Task.project_id == p.id).scalar() or 1
        done = db.query(func.count(Task.id)).filter(
            Task.project_id == p.id, Task.status == "done"
        ).scalar() or 0
        project_progress.append({
            "name": p.name,
            "progress": round(done / total * 100, 1),
            "total": total,
            "done": done,
            "status": p.status
        })

    # 最近一周完成情况
    week_ago = now - timedelta(days=7)
    weekly_data = []
    for i in range(7):
        d = week_ago + timedelta(days=i)
        next_d = d + timedelta(days=1)
        done = db.query(func.count(Task.id)).filter(
            Task.finished_date >= d, Task.finished_date < next_d
        ).scalar() or 0
        bugs_resolved = db.query(func.count(Bug.id)).filter(
            Bug.resolved_at >= d, Bug.resolved_at < next_d
        ).scalar() or 0
        weekly_data.append({
            "date": d.strftime("%m-%d"),
            "tasks_done": done,
            "bugs_resolved": bugs_resolved
        })

    # 我的待办
    my_tasks = db.query(Task).filter(
        Task.assigned_to == current_user.id,
        Task.status.in_(["todo", "doing"])
    ).count()
    my_bugs = db.query(Bug).filter(
        Bug.assigned_to == current_user.id,
        Bug.status == "active"
    ).count()

    # 团队活跃度
    recent_activities = db.query(Activity).order_by(
        Activity.created_at.desc()
    ).limit(20).all()
    activities = [{
        "id": a.id, "action": a.action, "object_type": a.object_type,
        "object_name": a.object_name, "created_at": a.created_at.strftime("%m-%d %H:%M") if a.created_at else ""
    } for a in recent_activities]

    return {
        "success": True,
        "data": {
            "total_projects": total_projects,
            "total_tasks": total_tasks,
            "active_tasks": active_tasks,
            "completed_tasks": completed_tasks,
            "total_bugs": total_bugs,
            "active_bugs": active_bugs,
            "resolved_bugs": resolved_bugs,
            "total_stories": total_stories,
            "active_stories": active_stories,
            "total_users": total_users,
            "project_progress": project_progress,
            "task_distribution": task_distribution,
            "bug_severity": bug_severity,
            "weekly_completed": weekly_data,
            "my_tasks": my_tasks,
            "my_bugs": my_bugs,
            "recent_activities": activities
        }
    }
