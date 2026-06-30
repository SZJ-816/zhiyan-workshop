"""成果转化评估 API路由 - 智研工坊"""
from fastapi import APIRouter, Query
from typing import Optional
from pydantic import BaseModel, Field
from app.services.transformation import transformation_service

router = APIRouter(prefix="/api/transformation", tags=["成果转化评估"])


class EvaluateRequest(BaseModel):
    project_id: Optional[int] = Field(None, description="项目ID")
    project_name: str = Field("", description="项目名称")


@router.get("/list")
def get_transformation_list():
    """获取成果转化评估列表

    GET /api/transformation/list
    """
    result = transformation_service.get_transformation_list()
    return {"success": True, "data": result, "total": len(result)}


@router.post("/evaluate")
def evaluate_transformation(req: EvaluateRequest):
    """评估成果转化潜力

    POST /api/transformation/evaluate
    Body: {"project_id": 1, "project_name": "智能数据分析平台"}
    """
    result = transformation_service.evaluate_transformation_potential(
        project_id=req.project_id,
        project_name=req.project_name,
    )
    return {"success": True, "data": result}


@router.get("/evaluate/{project_id}")
def get_evaluation(project_id: int):
    """获取单个项目转化评估结果

    GET /api/transformation/evaluate/1
    """
    result = transformation_service.evaluate_transformation_potential(
        project_id=project_id,
        project_name=f"项目{project_id}",
    )
    return {"success": True, "data": result}


@router.get("/industry-comparison")
def get_industry_comparison(score: float = Query(75.0, ge=50, le=100)):
    """获取行业对比数据

    GET /api/transformation/industry-comparison?score=75
    """
    result = transformation_service.get_industry_comparison(score)
    return {"success": True, "data": result}
