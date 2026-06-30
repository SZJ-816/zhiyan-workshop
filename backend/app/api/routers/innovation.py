"""创新能力评估 API路由 - 智研工坊"""
from fastapi import APIRouter, Query
from typing import Optional
from app.services.innovation import innovation_service

router = APIRouter(prefix="/api/innovation", tags=["创新能力评估"])


@router.get("/score")
def get_innovation_score(project_id: Optional[int] = Query(None, description="项目ID")):
    """获取创新指数评估

    GET /api/innovation/score?project_id=1
    """
    result = innovation_service.calculate_innovation_score(project_id)
    return {"success": True, "data": result}


@router.get("/trend")
def get_innovation_trend(days: int = Query(30, ge=7, le=90, description="天数")):
    """获取创新指数趋势

    GET /api/innovation/trend?days=30
    """
    result = innovation_service.get_trend_data(days)
    return {"success": True, "data": result}


@router.get("/suggestions")
def get_improvement_suggestions(project_id: Optional[int] = Query(None)):
    """获取创新能力提升建议

    GET /api/innovation/suggestions
    """
    suggestions = innovation_service.get_improvement_suggestions(project_id)
    return {"success": True, "data": suggestions}


@router.get("/dimensions")
def get_dimensions():
    """获取评估维度列表"""
    return {
        "success": True,
        "data": innovation_service.DIMENSIONS,
    }


@router.get("/overview")
def get_innovation_overview():
    """获取创新能力概览（仪表盘用）"""
    score = innovation_service.calculate_innovation_score()
    trend = innovation_service.get_trend_data(7)

    return {
        "success": True,
        "data": {
            "current_score": score["total_score"],
            "level": score["level"],
            "level_name": score["level_name"],
            "dimensions": score["dimensions"],
            "weekly_change": trend["change"],
            "weekly_change_percent": trend["change_percent"],
        },
    }
