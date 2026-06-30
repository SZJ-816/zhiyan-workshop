"""数据要素中台服务 - 智研工坊

研发数据资产化管理与价值度量
"""
import logging
import random
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class DataAssetService:
    """数据要素中台服务

    提供数据资产目录管理、价值度量、质量评估等
    """

    DATA_ASSETS = [
        {
            "key": "project_data",
            "name": "项目数据资产",
            "category": "项目数据",
            "description": "科研项目基本信息、里程碑、交付物等全生命周期数据",
            "value_level": 5,
            "quality_score": 95.2,
            "data_volume": 10,
            "data_unit": "个",
            "update_frequency": "实时",
            "sensitivity": "internal",
        },
        {
            "key": "task_data",
            "name": "任务数据资产",
            "category": "任务数据",
            "description": "研发任务清单、进度跟踪、工时消耗、分配关系等",
            "value_level": 4,
            "quality_score": 92.8,
            "data_volume": 110,
            "data_unit": "条",
            "update_frequency": "实时",
            "sensitivity": "internal",
        },
        {
            "key": "quality_data",
            "name": "质量数据资产",
            "category": "质量数据",
            "description": "缺陷库、测试用例、质量报告、缺陷修复轨迹等",
            "value_level": 5,
            "quality_score": 94.1,
            "data_volume": 32,
            "data_unit": "条",
            "update_frequency": "实时",
            "sensitivity": "internal",
        },
        {
            "key": "personnel_data",
            "name": "人员数据资产",
            "category": "人员数据",
            "description": "团队成员信息、技能画像、绩效数据、工时数据等",
            "value_level": 3,
            "quality_score": 85.6,
            "data_volume": 15,
            "data_unit": "人",
            "update_frequency": "每日",
            "sensitivity": "confidential",
        },
        {
            "key": "code_data",
            "name": "代码数据资产",
            "category": "代码数据",
            "description": "代码提交记录、版本历史、代码质量指标、技术债务等",
            "value_level": 4,
            "quality_score": 88.7,
            "data_volume": 256,
            "data_unit": "次",
            "update_frequency": "实时",
            "sensitivity": "confidential",
        },
        {
            "key": "ai_model_data",
            "name": "AI模型数据资产",
            "category": "模型数据",
            "description": "AI模型训练数据、预测结果、模型版本、性能指标等",
            "value_level": 5,
            "quality_score": 91.3,
            "data_volume": 4,
            "data_unit": "个",
            "update_frequency": "每周",
            "sensitivity": "confidential",
        },
    ]

    def __init__(self):
        self.total_calls = 3428
        self.asset_stats = {}

    def list_assets(self, category: Optional[str] = None) -> list:
        """获取数据资产列表"""
        assets = [dict(a) for a in self.DATA_ASSETS]
        if category:
            assets = [a for a in assets if a["category"] == category]
        return assets

    def get_asset_overview(self) -> dict:
        """获取数据资产概览"""
        assets = self.DATA_ASSETS
        total_volume = sum(a["data_volume"] for a in assets)
        avg_quality = sum(a["quality_score"] for a in assets) / len(assets)
        categories = list(set(a["category"] for a in assets))
        high_value_count = sum(1 for a in assets if a["value_level"] >= 4)

        return {
            "total_categories": len(categories),
            "total_assets": len(assets),
            "total_volume": total_volume,
            "avg_quality_score": round(avg_quality, 1),
            "high_value_count": high_value_count,
            "total_api_calls": self.total_calls,
            "categories": categories,
        }

    def get_value_metrics(self) -> dict:
        """获取数据要素价值度量指标"""
        return {
            "data_scale": {
                "total_records": 256000,
                "growth_rate": 15.8,
                "data_types": 6,
            },
            "data_quality": {
                "completeness": 92.5,
                "accuracy": 89.3,
                "timeliness": 94.7,
                "overall_score": 91.5,
            },
            "data_usage": {
                "api_calls": 3428,
                "model_invocations": 1286,
                "avg_response_ms": 120,
            },
            "value_transformation": {
                "data_driven_decisions": 89,
                "efficiency_improvement": 23.5,
                "cost_saving": 15.2,
            },
        }

    def get_data_pipeline_status(self) -> dict:
        """获取数据管道状态"""
        return {
            "ingestion": {
                "status": "running",
                "name": "数据采集层",
                "sources": ["MySQL禅道", "API接口", "日志系统"],
                "throughput": "1.2MB/s",
                "latency_ms": 50,
            },
            "processing": {
                "status": "running",
                "name": "数据处理层",
                "engines": ["Kafka", "Spark", "Flink"],
                "processing_speed": "8000条/秒",
            },
            "storage": {
                "status": "running",
                "name": "数据存储层",
                "databases": ["PostgreSQL", "Redis"],
                "storage_size": "2.3GB",
            },
            "application": {
                "status": "running",
                "name": "数据应用层",
                "applications": ["AI模型", "数据看板", "API服务"],
                "daily_calls": 1250,
            },
        }

    def get_trend_data(self, days: int = 30) -> dict:
        """获取数据资产增长趋势"""
        dates = []
        volumes = []
        calls = []
        base_volume = 180
        base_calls = 2000

        for i in range(days):
            date = (datetime.now() - timedelta(days=days - i - 1)).strftime("%m-%d")
            base_volume += random.uniform(2, 8)
            base_calls += random.randint(30, 80)
            dates.append(date)
            volumes.append(round(base_volume, 0))
            calls.append(base_calls)

        return {
            "dates": dates,
            "data_volume": volumes,
            "api_calls": calls,
        }


data_asset_service = DataAssetService()
