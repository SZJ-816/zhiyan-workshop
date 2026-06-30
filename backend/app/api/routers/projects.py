"""项目管理API（含任务管理）"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime
from app.core.database import get_db
from app.models.models import Project, Task, User
from app.schemas.schemas import ProjectOut, ProjectCreate, TaskOut, TaskCreate, TaskUpdate
from .auth import get_current_user

router = APIRouter(prefix="/api/projects", tags=["项目"])

@router.get("")
def list_projects(
    search: Optional[str] = None, status: Optional[str] = None,
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    q = db.query(Project)
    if search: q = q.filter(Project.name.contains(search))
    if status: q = q.filter(Project.status == status)
    total = q.count()
    items = q.order_by(Project.id.desc()).offset((page-1)*page_size).limit(page_size).all()
    result = []
    for p in items:
        done = db.query(func.count(Task.id)).filter(Task.project_id == p.id, Task.status == "done").scalar() or 0
        total_tasks = db.query(func.count(Task.id)).filter(Task.project_id == p.id).scalar() or 0
        d = ProjectOut.model_validate(p).model_dump()
        d["task_count"] = total_tasks
        d["task_done"] = done
        d["progress"] = round(done / total_tasks * 100, 1) if total_tasks > 0 else 0
        result.append(d)
    return {"success": True, "items": result, "total": total, "page": page, "page_size": page_size}

@router.post("")
def create_project(req: ProjectCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    p = Project(**req.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"success": True, "data": ProjectOut.model_validate(p).model_dump()}

@router.get("/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p: raise HTTPException(404, "项目不存在")
    all_tasks = db.query(func.count(Task.id)).filter(Task.project_id == project_id).scalar() or 0
    done_tasks = db.query(func.count(Task.id)).filter(
        Task.project_id == project_id, Task.status == "done"
    ).scalar() or 0
    data = ProjectOut.model_validate(p).model_dump()
    data["task_count"] = all_tasks
    data["task_done"] = done_tasks
    data["progress"] = round(done_tasks / all_tasks * 100, 1) if all_tasks > 0 else 0
    return {"success": True, "data": data}

@router.put("/{project_id}")
def update_project(project_id: int, data: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p: raise HTTPException(404, "项目不存在")
    for k, v in data.items():
        if hasattr(p, k): setattr(p, k, v)
    db.commit()
    return {"success": True}

# ===== 全部任务（放在 /{project_id}/tasks 之前，避免路径冲突）=====
@router.get("/tasks")
def list_all_tasks(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    assigned_to: Optional[int] = None,
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    q = db.query(Task)
    if project_id: q = q.filter(Task.project_id == project_id)
    if status: q = q.filter(Task.status == status)
    if assigned_to: q = q.filter(Task.assigned_to == assigned_to)
    total = q.count()
    items = q.order_by(Task.priority.desc(), Task.id.desc()).offset((page-1)*page_size).limit(page_size).all()
    result = []
    for t in items:
        d = TaskOut.model_validate(t).model_dump()
        if t.assigned_to:
            u = db.query(User).filter(User.id == t.assigned_to).first()
            d["assignee_name"] = u.realname if u else ""
        d["project_name"] = t.project.name if t.project else ""
        result.append(d)
    return {"success": True, "items": result, "total": total, "page": page, "page_size": page_size}

# ===== 任务管理 =====
@router.get("/{project_id}/tasks")
def list_tasks(
    project_id: int,
    status: Optional[str] = None,
    assigned_to: Optional[int] = None,
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    q = db.query(Task).filter(Task.project_id == project_id)
    if status: q = q.filter(Task.status == status)
    if assigned_to: q = q.filter(Task.assigned_to == assigned_to)
    total = q.count()
    items = q.order_by(Task.priority.desc(), Task.id.desc()).offset((page-1)*page_size).limit(page_size).all()
    # Join with user names
    result = []
    for t in items:
        d = TaskOut.model_validate(t).model_dump()
        if t.assigned_to:
            u = db.query(User).filter(User.id == t.assigned_to).first()
            d["assignee_name"] = u.realname if u else ""
        result.append(d)
    status_counts = {
        "todo": db.query(func.count(Task.id)).filter(Task.project_id == project_id, Task.status == "todo").scalar() or 0,
        "doing": db.query(func.count(Task.id)).filter(Task.project_id == project_id, Task.status == "doing").scalar() or 0,
        "done": db.query(func.count(Task.id)).filter(Task.project_id == project_id, Task.status == "done").scalar() or 0,
        "closed": db.query(func.count(Task.id)).filter(Task.project_id == project_id, Task.status == "closed").scalar() or 0,
    }
    return {"success": True, "items": result, "total": total, "page": page, "page_size": page_size, "status_counts": status_counts}

@router.post("/{project_id}/tasks")
def create_task(project_id: int, req: TaskCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    data = req.model_dump()
    data.pop("project_id", None)  # project_id from URL, remove from body to avoid duplicate
    t = Task(**data, project_id=project_id)
    db.add(t)
    db.commit()
    db.refresh(t)
    return {"success": True, "data": TaskOut.model_validate(t).model_dump()}

@router.put("/tasks/{task_id}")
def update_task(task_id: int, data: TaskUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    t = db.query(Task).filter(Task.id == task_id).first()
    if not t: raise HTTPException(404, "任务不存在")
    update_data = data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        if hasattr(t, k): setattr(t, k, v)
    if data.status == "done" and not t.finished_date:
        t.finished_date = datetime.now()
    db.commit()
    return {"success": True}

@router.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    t = db.query(Task).filter(Task.id == task_id).first()
    if not t: raise HTTPException(404, "任务不存在")
    db.delete(t)
    db.commit()
    return {"success": True}
