"""产品管理API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from app.core.database import get_db
from app.models.models import Product, Story
from app.schemas.schemas import ProductOut, ProductCreate, StoryOut, StoryCreate, PaginatedResponse
from .auth import get_current_user

router = APIRouter(prefix="/api/products", tags=["产品"])

@router.get("")
def list_products(
    search: Optional[str] = None, status: Optional[str] = None,
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    q = db.query(Product)
    if search:
        q = q.filter(Product.name.contains(search) | Product.code.contains(search))
    if status:
        q = q.filter(Product.status == status)
    total = q.count()
    items = q.order_by(Product.id.desc()).offset((page-1)*page_size).limit(page_size).all()
    return {"success": True, "items": [ProductOut.model_validate(p).model_dump() for p in items], "total": total, "page": page, "page_size": page_size}

@router.post("")
def create_product(req: ProductCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    p = Product(**req.model_dump(), created_by=current_user.id)
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"success": True, "data": ProductOut.model_validate(p).model_dump()}

@router.get("/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p: raise HTTPException(404, "产品不存在")
    story_count = db.query(func.count(Story.id)).filter(Story.product_id == product_id).scalar()
    data = ProductOut.model_validate(p).model_dump()
    data["story_count"] = story_count
    return {"success": True, "data": data}

# ===== 需求(Stories) =====
@router.get("/{product_id}/stories")
def list_stories(
    product_id: int, status: Optional[str] = None,
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    q = db.query(Story).filter(Story.product_id == product_id)
    if status: q = q.filter(Story.status == status)
    total = q.count()
    items = q.order_by(Story.priority.desc(), Story.id.desc()).offset((page-1)*page_size).limit(page_size).all()
    return {"success": True, "items": [StoryOut.model_validate(s).model_dump() for s in items], "total": total, "page": page, "page_size": page_size}

@router.post("/{product_id}/stories")
def create_story(product_id: int, req: StoryCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    s = Story(**req.model_dump(), product_id=product_id, created_by=current_user.id)
    db.add(s)
    db.commit()
    db.refresh(s)
    return {"success": True, "data": StoryOut.model_validate(s).model_dump()}

@router.put("/stories/{story_id}")
def update_story(story_id: int, data: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    s = db.query(Story).filter(Story.id == story_id).first()
    if not s: raise HTTPException(404, "需求不存在")
    for k, v in data.items():
        if hasattr(s, k): setattr(s, k, v)
    db.commit()
    return {"success": True}
