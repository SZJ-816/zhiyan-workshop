"""
AI 推理服务 — 使用训练好的模型进行预测

三个预测 API:
1. predict_bug_severity(title) → {severity, confidence}
2. predict_task_duration(estimate, priority, project_id, assignee) → {predicted_hours, range}
3. predict_project_risk(project_id) → {risk_level, health_score, factors}
"""
import json
import pickle
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np
import pymysql

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

MODEL_DIR = Path("/app/ai_models")
MYSQL_CONFIG = {
    "host": "zentao-mysql",
    "port": 3306,
    "user": "zentao",
    "password": "zentao123",
    "database": "zentao",
    "charset": "utf8mb4",
}


class ZentaoPredictor:
    """禅道 AI 预测器"""

    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.encoders: Dict[str, Any] = {}
        self._load_models()
        self.training_count = 0
        self.prediction_count = 0

    def _load_models(self):
        """加载训练好的模型"""
        model_files = {
            "bug_severity": ("bug_severity_model.pkl", "bug_severity_encoder.pkl"),
            "task_duration": ("task_duration_model.pkl", None),
            "project_risk": ("project_risk_model.pkl", "project_risk_encoder.pkl"),
        }
        for name, (model_file, encoder_file) in model_files.items():
            model_path = MODEL_DIR / model_file
            if model_path.exists():
                with open(model_path, "rb") as f:
                    self.models[name] = pickle.load(f)
                    log.info(f"模型已加载: {name}")
            if encoder_file:
                encoder_path = MODEL_DIR / encoder_file
                if encoder_path.exists():
                    with open(encoder_path, "rb") as f:
                        self.encoders[name] = pickle.load(f)

        # 加载元数据
        meta_path = MODEL_DIR / "model_metadata.json"
        if meta_path.exists():
            with open(meta_path, "r") as f:
                meta = json.load(f)
                self.training_count = 1
                self.current_model = "RandomForest + GradientBoosting"
        else:
            self.current_model = "rule_based_v0"

    def is_model_loaded(self) -> bool:
        return len(self.models) > 0 or self.current_model != "rule_based_v0"

    # ========== Bug 严重度预测 ==========

    def predict_bug_severity(self, title: str) -> Dict[str, Any]:
        """预测 Bug 严重度"""
        if not title:
            return {"severity": "normal", "confidence": 0.0, "method": "default"}

        model = self.models.get("bug_severity")

        # 规则模型
        if isinstance(model, dict) and model.get("type") == "keyword_rules":
            return self._keyword_predict(title, model["rules"])

        # RF 模型
        if model and hasattr(model, "predict_proba"):
            try:
                features = self._extract_bug_features(title)
                probs = model.predict_proba([features])[0]
                severity = model.predict([features])[0]
                encoder = self.encoders.get("bug_severity")
                if encoder:
                    severity_label = encoder.inverse_transform([severity])[0]
                else:
                    severity_label = str(severity)
                confidence = float(max(probs))
                self.prediction_count += 1
                return {
                    "severity": severity_label,
                    "confidence": round(confidence, 3),
                    "method": "RandomForest",
                    "probabilities": {str(k): round(float(v), 3) for k, v in zip(
                        encoder.classes_ if encoder else range(len(probs)), probs
                    )}
                }
            except Exception as e:
                log.error(f"Bug 预测失败: {e}")

        # 兜底
        return self._keyword_predict(title, None)

    def _extract_bug_features(self, title: str) -> str:
        """提取 Bug 文本特征"""
        keywords = {
            "fatal":   ["崩溃", "死机", "数据丢失", "安全漏洞", "资金", "越权", "注入"],
            "serious": ["超时", "白屏", "报错", "500", "无法", "异常", "错误", "失败"],
            "normal":  ["显示", "样式", "偏移", "乱码", "格式", "排列", "排序"],
            "minor":   ["拼写", "颜色", "间距", "提示", "文案", "建议"],
        }
        features = []
        for level in ["fatal", "serious", "normal", "minor"]:
            hits = sum(1 for kw in keywords[level] if kw in title)
            features.append(str(hits))
        features.append(str(len(title)))
        features.append(str(1) if any(c.isascii() and not c.isalpha() for c in title) else str(0))
        return " ".join(features)

    def _keyword_predict(self, title: str, rules: Optional[Dict] = None) -> Dict:
        """基于关键词的预测 (后备方案)"""
        if rules is None:
            rules = {
                "fatal":   ["崩溃", "死机", "数据丢失", "安全漏洞", "资金", "越权", "注入", "fatal"],
                "serious": ["超时", "白屏", "报错", "500", "无法", "异常", "错误", "失败", "serious"],
                "normal":  ["显示", "样式", "偏移", "乱码", "格式", "排列", "排序", "normal"],
                "minor":   ["拼写", "颜色", "间距", "提示", "文案", "建议", "minor"],
            }
        title_lower = title.lower()
        scores = {}
        for level, keywords in rules.items():
            scores[level] = sum(1 for kw in keywords if kw in title_lower or kw.lower() in title_lower)

        best = max(scores, key=scores.get)
        total = sum(scores.values()) or 1
        confidence = scores[best] / (total if total > 0 else 1)

        if confidence < 0.3:
            best = "normal"
            confidence = 0.5

        self.prediction_count += 1
        return {
            "severity": best,
            "confidence": round(confidence, 3),
            "method": "keyword_rules",
            "scores": scores,
        }

    # ========== 任务耗时预测 ==========

    def predict_task_duration(
        self, estimate: float, priority: str, project_id: int, assigned_to: int
    ) -> Dict[str, Any]:
        """预测任务完成耗时"""
        priority_map = {"high": 4, "medium": 3, "low": 2, "urgent": 5}
        priority_val = priority_map.get(priority, 3)

        features = np.array([[estimate, priority_val, project_id, assigned_to]])
        model = self.models.get("task_duration")

        if model and hasattr(model, "predict"):
            try:
                predicted = float(model.predict(features)[0])
                predicted = max(predicted, estimate * 0.5)
                self.prediction_count += 1
                return {
                    "predicted_hours": round(predicted, 1),
                    "estimate_hours": estimate,
                    "range_low": round(predicted * 0.75, 1),
                    "range_high": round(predicted * 1.5, 1),
                    "method": "GradientBoosting",
                }
            except Exception as e:
                log.error(f"任务预测失败: {e}")

        # 兜底: 基于优先级的经验公式
        multiplier = {"urgent": 0.7, "high": 0.85, "medium": 1.0, "low": 1.3}
        predicted = estimate * multiplier.get(priority, 1.0)
        return {
            "predicted_hours": round(predicted, 1),
            "estimate_hours": estimate,
            "range_low": round(predicted * 0.7, 1),
            "range_high": round(predicted * 1.5, 1),
            "method": "heuristic",
        }

    # ========== 项目风险预测 ==========

    def predict_project_risk(self, project_id: int) -> Dict[str, Any]:
        """预测项目风险"""
        # 获取项目统计数据
        try:
            conn = pymysql.connect(**MYSQL_CONFIG)
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            cursor.execute("SELECT * FROM zt_project WHERE id=%s", (project_id,))
            project = cursor.fetchone()

            if not project:
                return {"error": "项目不存在"}

            cursor.execute(
                "SELECT COUNT(*) as total, SUM(CASE WHEN status='done' THEN 1 ELSE 0 END) as done FROM zt_task WHERE project_id=%s",
                (project_id,))
            task_stats = cursor.fetchone()

            cursor.execute(
                "SELECT COUNT(*) as total, SUM(CASE WHEN status='resolved' THEN 1 ELSE 0 END) as resolved FROM zt_bug WHERE project_id=%s",
                (project_id,))
            bug_stats = cursor.fetchone()

            conn.close()

            task_total = int(task_stats["total"] or 0)
            task_done = int(task_stats["done"] or 0)
            bug_total = int(bug_stats["total"] or 0)
            bug_resolved = int(bug_stats["resolved"] or 0)

            completion_rate = task_done / task_total if task_total > 0 else 0
            bug_rate = bug_resolved / bug_total if bug_total > 0 else 0

            features = np.array([[task_total, task_done, bug_total, bug_resolved,
                                  completion_rate, bug_rate]])

            model = self.models.get("project_risk")
            health_score = completion_rate * 40 + bug_rate * 30 + max(0, 30 - (max(0, task_total - task_done) * 2))

            risk_level = "low"
            if health_score < 25:
                risk_level = "critical"
            elif health_score < 50:
                risk_level = "high"
            elif health_score < 75:
                risk_level = "medium"

            if model and hasattr(model, "predict"):
                try:
                    predicted_risk = int(model.predict(features)[0])
                    # 训练时 label: 0=low, 1=medium, 2=high, 3=critical
                    risk_map = {0: "low", 1: "medium", 2: "high", 3: "critical"}
                    risk_level = risk_map.get(predicted_risk, "medium")
                    self.prediction_count += 1
                except Exception:
                    pass

            factors = []
            if completion_rate < 0.5:
                factors.append("任务完成率偏低")
            if bug_rate < 0.5:
                factors.append("Bug 解决率不足")
            if task_total - task_done > 10:
                factors.append("积压任务过多")
            if bug_total - bug_resolved > 5:
                factors.append("未解决 Bug 较多")

            return {
                "project_id": project_id,
                "project_name": project["name"],
                "risk_level": risk_level,
                "health_score": round(health_score, 1),
                "completion_rate": round(completion_rate * 100, 1),
                "bug_resolve_rate": round(bug_rate * 100, 1),
                "task_total": task_total,
                "task_done": task_done,
                "bug_total": bug_total,
                "bug_resolved": bug_resolved,
                "risk_factors": factors,
                "method": "RandomForest" if model else "heuristic",
            }
        except Exception as e:
            log.error(f"项目风险预测失败: {e}")
            return {"error": str(e)}

    # ========== 数据洞察 ==========

    def get_data_insights(self) -> Dict[str, Any]:
        """获取系统数据洞察"""
        try:
            conn = pymysql.connect(**MYSQL_CONFIG)
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            insights = {}

            # 任务统计
            cursor.execute("SELECT status, COUNT(*) as cnt FROM zt_task GROUP BY status")
            task_status = {r["status"]: r["cnt"] for r in cursor.fetchall()}
            insights["task_distribution"] = task_status

            # Bug严重度分布
            cursor.execute("SELECT severity, COUNT(*) as cnt FROM zt_bug GROUP BY severity")
            bug_severity = {str(r["severity"]): r["cnt"] for r in cursor.fetchall()}
            insights["bug_severity_distribution"] = bug_severity

            # 项目进度
            cursor.execute("SELECT status, COUNT(*) as cnt FROM zt_project GROUP BY status")
            project_status = {r["status"]: r["cnt"] for r in cursor.fetchall()}
            insights["project_status"] = project_status

            # 总量
            cursor.execute("SELECT COUNT(*) as cnt FROM zt_user")
            insights["total_users"] = cursor.fetchone()["cnt"]
            cursor.execute("SELECT COUNT(*) as cnt FROM zt_product")
            insights["total_products"] = cursor.fetchone()["cnt"]
            cursor.execute("SELECT COUNT(*) as cnt FROM zt_story")
            insights["total_stories"] = cursor.fetchone()["cnt"]

            conn.close()
            return insights
        except Exception as e:
            return {"error": str(e)}


# 全局单例
predictor = ZentaoPredictor()
