"""Bug管理API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime
from app.core.database import get_db
from app.models.models import Bug, User, Project, Product
from app.schemas.schemas import BugOut, BugCreate
from .auth import get_current_user

router = APIRouter(prefix="/api/bugs", tags=["Bug"])

@router.get("")
def list_bugs(
    search: Optional[str] = None, status: Optional[str] = None, severity: Optional[str] = None,
    product_id: Optional[int] = None, project_id: Optional[int] = None,
    assigned_to: Optional[int] = None,
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    q = db.query(Bug)
    if search: q = q.filter(Bug.title.contains(search))
    if status: q = q.filter(Bug.status == status)
    if severity: q = q.filter(Bug.severity == severity)
    if product_id: q = q.filter(Bug.product_id == product_id)
    if project_id: q = q.filter(Bug.project_id == project_id)
    if assigned_to: q = q.filter(Bug.assigned_to == assigned_to)
    total = q.count()
    items = q.order_by(Bug.severity.desc(), Bug.id.desc()).offset((page-1)*page_size).limit(page_size).all()
    result = []
    for b in items:
        d = BugOut.model_validate(b).model_dump()
        if b.assigned_to:
            u = db.query(User).filter(User.id == b.assigned_to).first()
            d["assignee_name"] = u.realname if u else ""
        if b.product_id:
            p = db.query(Product).filter(Product.id == b.product_id).first()
            d["product_name"] = p.name if p else ""
        result.append(d)
    
    sev_counts = {}
    for s, n in db.query(Bug.severity, func.count(Bug.id)).filter(Bug.status != "closed").group_by(Bug.severity).all():
        sev_counts[s] = n
    
    return {"success": True, "items": result, "total": total, "page": page, "page_size": page_size, "severity_counts": sev_counts}

@router.post("")
def create_bug(req: BugCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    b = Bug(**req.model_dump(), created_by=current_user.id)
    db.add(b)
    db.commit()
    db.refresh(b)
    return {"success": True, "data": BugOut.model_validate(b).model_dump()}

@router.get("/{bug_id}")
def get_bug(bug_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    b = db.query(Bug).filter(Bug.id == bug_id).first()
    if not b: raise HTTPException(404, "Bug不存在")
    return {"success": True, "data": BugOut.model_validate(b).model_dump()}

@router.put("/{bug_id}")
def update_bug(bug_id: int, data: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    b = db.query(Bug).filter(Bug.id == bug_id).first()
    if not b: raise HTTPException(404, "Bug不存在")
    for k, v in data.items():
        if hasattr(b, k): setattr(b, k, v)
    if data.get("status") == "resolved" and not b.resolved_at:
        b.resolved_at = datetime.now()
    if data.get("status") == "closed" and not b.closed_at:
        b.closed_at = datetime.now()
    db.commit()
    return {"success": True}

@router.delete("/{bug_id}")
def delete_bug(bug_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    b = db.query(Bug).filter(Bug.id == bug_id).first()
    if not b: raise HTTPException(404, "Bug不存在")
    db.delete(b)
    db.commit()
    return {"success": True}
