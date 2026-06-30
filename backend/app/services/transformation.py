"""成果转化评估服务 - 智研工坊

科研成果转化潜力评估与路径推荐
"""
import logging
import random
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class TransformationService:
    """成果转化评估服务

    评估科研成果的转化潜力，提供转化路径建议
    """

    TRANSFORMATION_DIMENSIONS = [
        {"key": "tech_maturity", "name": "技术成熟度", "weight": 0.25},
        {"key": "market_demand", "name": "市场需求度", "weight": 0.25},
        {"key": "innovation_level", "name": "创新水平", "weight": 0.20},
        {"key": "team_capability", "name": "团队能力", "weight": 0.15},
        {"key": "resource_support", "name": "资源支撑", "weight": 0.15},
    ]

    def __init__(self):
        self.evaluation_records = []

    def evaluate_transformation_potential(
        self, project_id: Optional[int] = None, project_name: str = ""
    ) -> dict:
        """评估成果转化潜力

        Args:
            project_id: 项目ID
            project_name: 项目名称

        Returns:
            转化潜力评估结果
        """
        dimensions = {}
        total_score = 0

        for dim in self.TRANSFORMATION_DIMENSIONS:
            score = self._calculate_dimension(dim["key"])
            dimensions[dim["key"]] = {
                "name": dim["name"],
                "score": score,
                "weight": dim["weight"],
                "weighted_score": round(score * dim["weight"], 2),
            }
            total_score += score * dim["weight"]

        total_score = round(total_score, 1)
        potential_level = self._get_potential_level(total_score)

        result = {
            "project_id": project_id,
            "project_name": project_name or "未命名项目",
            "total_score": total_score,
            "potential_level": potential_level["level"],
            "potential_name": potential_level["name"],
            "description": potential_level["desc"],
            "dimensions": dimensions,
            "suggested_paths": self._get_suggested_paths(total_score),
            "estimated_roi": round(random.uniform(1.5, 4.5), 1),
            "estimated_cycle_months": random.randint(6, 24),
            "evaluated_at": datetime.now().isoformat(),
        }

        self.evaluation_records.append(result)
        return result

    def _calculate_dimension(self, dimension_key: str) -> float:
        """计算单个维度得分"""
        base_scores = {
            "tech_maturity": 72,
            "market_demand": 68,
            "innovation_level": 85,
            "team_capability": 78,
            "resource_support": 65,
        }
        base = base_scores.get(dimension_key, 70)
        variation = random.uniform(-8, 8)
        return round(max(50, min(95, base + variation)), 1)

    def _get_potential_level(self, score: float) -> dict:
        """获取转化潜力等级"""
        if score >= 85:
            return {
                "level": "S",
                "name": "极高潜力",
                "desc": "成果转化价值极高，建议快速推进产业化",
            }
        elif score >= 75:
            return {
                "level": "A",
                "name": "高潜力",
                "desc": "成果转化价值较高，具备良好商业化前景",
            }
        elif score >= 65:
            return {
                "level": "B",
                "name": "中潜力",
                "desc": "有一定转化价值，需进一步完善后推进",
            }
        elif score >= 55:
            return {
                "level": "C",
                "name": "一般潜力",
                "desc": "转化价值有限，建议持续优化迭代",
            }
        else:
            return {
                "level": "D",
                "name": "低潜力",
                "desc": "当前转化条件不成熟，建议继续研发积累",
            }

    def _get_suggested_paths(self, score: float) -> list:
        """获取转化路径建议"""
        paths = [
            {
                "type": "technology_transfer",
                "name": "技术转让",
                "description": "将技术成果转让给企业进行产业化",
                "suitability": round(random.uniform(60, 90), 1),
            },
            {
                "type": "cooperative_development",
                "name": "合作开发",
                "description": "与企业联合开发，共同推进成果转化",
                "suitability": round(random.uniform(65, 92), 1),
            },
            {
                "type": "spin_off",
                "name": "孵化创业",
                "description": "成立创业公司，自主推进成果产业化",
                "suitability": round(random.uniform(55, 85), 1),
            },
            {
                "type": "licensing",
                "name": "许可授权",
                "description": "通过技术许可方式授权企业使用",
                "suitability": round(random.uniform(60, 88), 1),
            },
        ]
        return sorted(paths, key=lambda x: x["suitability"], reverse=True)

    def get_transformation_list(self) -> list:
        """获取成果转化评估列表"""
        projects = [
            {"id": 1, "name": "智能数据分析平台", "score": 82.5, "level": "A"},
            {"id": 2, "name": "云原生微服务架构", "score": 76.3, "level": "A"},
            {"id": 3, "name": "AI智能客服系统", "score": 71.8, "level": "B"},
            {"id": 4, "name": "区块链存证系统", "score": 68.2, "level": "B"},
            {"id": 5, "name": "移动端协同办公", "score": 65.4, "level": "B"},
            {"id": 6, "name": "DevOps自动化平台", "score": 79.6, "level": "A"},
        ]
        return projects

    def get_industry_comparison(self, score: float) -> dict:
        """获取行业对比数据"""
        return {
            "your_score": score,
            "industry_avg": 68.5,
            "top_20_percent": 82.0,
            "top_10_percent": 88.5,
            "percentile": round((score - 50) / 50 * 100, 1),
            "similar_projects": random.randint(20, 80),
            "success_rate": round(random.uniform(40, 75), 1),
        }


transformation_service = TransformationService()
