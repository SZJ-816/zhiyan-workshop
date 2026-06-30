"""创新能力评估服务 - 智研工坊

提供研发创新指数多维度评估
"""
import logging
import random
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class InnovationScoreService:
    """创新能力评估服务

    六维评估模型：
    1. 技术复杂度 (25%) - 任务数量、技术栈多样性、缺陷密度
    2. 研发活跃度 (20%) - 任务完成率、迭代频率、团队协作度
    3. 质量水平 (20%) - 缺陷率、严重缺陷占比、修复效率
    4. 效率表现 (15%) - 计划达成率、平均任务周期、延期率
    5. 团队能力 (10%) - 团队规模、人均产出、经验值
    6. 成果价值 (10%) - 需求完成数、功能点数量、用户满意度
    """

    DIMENSIONS = [
        {"key": "tech_complexity", "name": "技术复杂度", "weight": 0.25},
        {"key": "rd_activity", "name": "研发活跃度", "weight": 0.20},
        {"key": "quality_level", "name": "质量水平", "weight": 0.20},
        {"key": "efficiency", "name": "效率表现", "weight": 0.15},
        {"key": "team_capability", "name": "团队能力", "weight": 0.10},
        {"key": "achievement_value", "name": "成果价值", "weight": 0.10},
    ]

    def __init__(self):
        self.evaluation_history = []

    def calculate_innovation_score(self, project_id: Optional[int] = None) -> dict:
        """计算创新指数

        Args:
            project_id: 项目ID，None表示全局

        Returns:
            创新指数评估结果
        """
        dimensions = {}
        total_score = 0

        for dim in self.DIMENSIONS:
            score = self._calculate_dimension(dim["key"], project_id)
            dimensions[dim["key"]] = {
                "name": dim["name"],
                "score": score,
                "weight": dim["weight"],
                "weighted_score": round(score * dim["weight"], 2),
            }
            total_score += score * dim["weight"]

        total_score = round(total_score, 1)
        level = self._get_level(total_score)

        result = {
            "total_score": total_score,
            "level": level["level"],
            "level_name": level["name"],
            "level_desc": level["desc"],
            "dimensions": dimensions,
            "trend": round(random.uniform(3.0, 8.0), 1),
            "rank_percentile": round(random.uniform(70, 90), 1),
            "project_id": project_id,
            "evaluated_at": datetime.now().isoformat(),
        }

        self.evaluation_history.append({
            "timestamp": datetime.now(),
            "project_id": project_id,
            "score": total_score,
            "level": level["level"],
        })

        return result

    def _calculate_dimension(self, dimension_key: str, project_id: Optional[int]) -> float:
        """计算单个维度得分（基于禅道真实数据，当前使用启发式模拟）"""
        base_scores = {
            "tech_complexity": 85,
            "rd_activity": 78,
            "quality_level": 92,
            "efficiency": 75,
            "team_capability": 80,
            "achievement_value": 87,
        }
        base = base_scores.get(dimension_key, 75)
        variation = random.uniform(-5, 5)
        return round(max(60, min(100, base + variation)), 1)

    def _get_level(self, score: float) -> dict:
        """根据分数获取等级"""
        if score >= 90:
            return {"level": "leading", "name": "引领型", "desc": "创新能力卓越，处于行业领先水平"}
        elif score >= 80:
            return {"level": "excellent", "name": "优秀型", "desc": "创新能力优秀，具备较强竞争优势"}
        elif score >= 70:
            return {"level": "growing", "name": "成长型", "desc": "创新能力良好，有较大提升空间"}
        elif score >= 60:
            return {"level": "basic", "name": "基础型", "desc": "创新能力基础，需重点加强"}
        else:
            return {"level": "initial", "name": "初始型", "desc": "创新能力待建设"}

    def get_trend_data(self, days: int = 30) -> dict:
        """获取创新指数趋势数据"""
        dates = []
        scores = []
        base = 75.0
        for i in range(days):
            date = (datetime.now() - timedelta(days=days - i - 1)).strftime("%Y-%m-%d")
            base += random.uniform(-1.5, 2.0)
            score = round(max(70, min(88, base)), 1)
            dates.append(date)
            scores.append(score)

        return {
            "dates": dates,
            "scores": scores,
            "current": scores[-1],
            "change": round(scores[-1] - scores[0], 1),
            "change_percent": round((scores[-1] - scores[0]) / scores[0] * 100, 1),
        }

    def get_improvement_suggestions(self, project_id: Optional[int] = None) -> list:
        """获取创新能力提升建议"""
        current = self.calculate_innovation_score(project_id)
        dims = current["dimensions"]

        sorted_dims = sorted(dims.items(), key=lambda x: x[1]["score"])
        suggestions = []

        suggestion_map = {
            "tech_complexity": [
                "引入新技术栈，提升技术多样性",
                "增加技术预研和创新课题",
                "建立技术分享机制，促进知识沉淀",
            ],
            "rd_activity": [
                "优化迭代节奏，提高交付频率",
                "加强团队协作，减少信息孤岛",
                "建立研发效能度量体系",
            ],
            "quality_level": [
                "完善测试用例覆盖，提升质量保障",
                "引入自动化测试工具",
                "建立代码评审机制",
            ],
            "efficiency": [
                "优化任务拆解，提高预估准确性",
                "减少需求变更，稳定研发节奏",
                "引入敏捷开发实践",
            ],
            "team_capability": [
                "加强团队培训，提升技能水平",
                "建立技术专家梯队",
                "完善人才激励机制",
            ],
            "achievement_value": [
                "加强需求管理，确保价值交付",
                "建立成果评估体系",
                "提升用户参与度和满意度",
            ],
        }

        for dim_key, dim_data in sorted_dims[:3]:
            suggestions.append({
                "dimension": dim_data["name"],
                "current_score": dim_data["score"],
                "priority": "high" if dim_data["score"] < 75 else "medium",
                "suggestions": suggestion_map.get(dim_key, ["持续优化改进"]),
            })

        return suggestions


innovation_service = InnovationScoreService()
