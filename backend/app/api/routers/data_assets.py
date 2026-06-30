"""数据要素中台 API路由 - 智研工坊"""
from fastapi import APIRouter, Query
from typing import Optional
from app.services.data_asset import data_asset_service

router = APIRouter(prefix="/api/data-assets", tags=["数据要素中台"])


@router.get("/overview")
def get_asset_overview():
    """获取数据资产概览

    GET /api/data-assets/overview
    """
    result = data_asset_service.get_asset_overview()
    return {"success": True, "data": result}


@router.get("/list")
def list_assets(category: Optional[str] = Query(None, description="数据类别")):
    """获取数据资产列表

    GET /api/data-assets/list?category=项目数据
    """
    assets = data_asset_service.list_assets(category)
    return {"success": True, "data": assets, "total": len(assets)}


@router.get("/value-metrics")
def get_value_metrics():
    """获取数据要素价值度量指标

    GET /api/data-assets/value-metrics
    """
    result = data_asset_service.get_value_metrics()
    return {"success": True, "data": result}


@router.get("/pipeline-status")
def get_pipeline_status():
    """获取数据管道状态

    GET /api/data-assets/pipeline-status
    """
    result = data_asset_service.get_data_pipeline_status()
    return {"success": True, "data": result}


@router.get("/trend")
def get_asset_trend(days: int = Query(30, ge=7, le=90)):
    """获取数据资产增长趋势

    GET /api/data-assets/trend?days=30
    """
    result = data_asset_service.get_trend_data(days)
    return {"success": True, "data": result}


@router.get("/dashboard")
def get_data_dashboard():
    """获取数据要素中台仪表盘数据（综合）"""
    overview = data_asset_service.get_asset_overview()
    metrics = data_asset_service.get_value_metrics()
    pipeline = data_asset_service.get_data_pipeline_status()
    assets = data_asset_service.list_assets()

    return {
        "success": True,
        "data": {
            "overview": overview,
            "metrics": metrics,
            "pipeline": pipeline,
            "assets": assets,
        },
    }
