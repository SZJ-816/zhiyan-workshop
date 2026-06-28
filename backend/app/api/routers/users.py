"""用户管理API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from passlib.context import CryptContext
from app.core.database import get_db
from app.models.models import User, Department, Task
from app.schemas.schemas import UserOut, UserCreate, DepartmentOut, DepartmentCreate
from .auth import get_current_user

router = APIRouter(prefix="/api/users", tags=["用户"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.get("")
def list_users(
    search: Optional[str] = None, role: Optional[str] = None,
    department_id: Optional[int] = None,
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    q = db.query(User)
    if search: q = q.filter(User.realname.contains(search) | User.account.contains(search))
    if role: q = q.filter(User.role == role)
    if department_id: q = q.filter(User.department_id == department_id)
    total = q.count()
    items = q.order_by(User.id).offset((page-1)*page_size).limit(page_size).all()
    result = []
    for u in items:
        d = UserOut.model_validate(u).model_dump()
        if u.department_id:
            dept = db.query(Department).filter(Department.id == u.department_id).first()
            d["department_name"] = dept.name if dept else ""
        result.append(d)
    return {"success": True, "items": result, "total": total, "page": page, "page_size": page_size}

@router.post("")
def create_user(req: UserCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if db.query(User).filter(User.account == req.account).first():
        raise HTTPException(400, "账号已存在")
    user = User(**req.model_dump(), password=pwd_context.hash(req.password))
    db.add(user)
    db.commit()
    return {"success": True, "data": UserOut.model_validate(user).model_dump()}

# ===== 部门 =====
@router.get("/departments")
def list_departments(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    depts = db.query(Department).order_by(Department.sort).all()
    return {
        "success": True,
        "items": [{"id": d.id, "name": d.name, "parent_id": d.parent_id, "sort": d.sort} for d in depts]
    }

@router.post("/departments")
def create_department(req: DepartmentCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    d = Department(**req.model_dump())
    db.add(d)
    db.commit()
    return {"success": True, "data": {"id": d.id, "name": d.name}}

# ===== 报表数据 =====
@router.get("/reports/task-by-user")
def task_by_user(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    data = db.query(
        User.realname,
        func.count(Task.id).label("total"),
        func.sum(func.if_(Task.status == "done", 1, 0)).label("done")
    ).outerjoin(Task, Task.assigned_to == User.id).group_by(User.id).all()
    return {"success": True, "items": [
        {"name": n or "未知", "total": int(t or 0), "done": int(d or 0)} for n, t, d in data
    ]}
