"""
AI 模型训练 — 基于禅道系统真实数据

三个预测模型:
1. BugSeverityClassifier  — NLP特征 + 文本分类 → 预测 Bug 严重度
2. TaskDurationRegressor  — 多特征回归 → 预测任务完成耗时
3. ProjectRiskClassifier  — 多维特征分类 → 预测项目风险等级

数据来源: 禅道 MySQL (zt_task, zt_bug, zt_project)
"""
import json
import pickle
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

import numpy as np
import pymysql
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report, mean_absolute_error, r2_score

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


class ZentaoAITrainer:
    """禅道 AI 模型训练器"""

    def __init__(self):
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        self.conn = pymysql.connect(**MYSQL_CONFIG)
        self.models: Dict[str, Any] = {}
        self.label_encoders: Dict[str, LabelEncoder] = {}

    # ========== 数据抽取 ==========

    def fetch_tasks(self) -> List[Dict]:
        """抽取任务数据 (含完成时间)"""
        cursor = self.conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT id, name, status, priority, project_id, assigned_to,
                   estimate, consumed, start_date, finished_date, created_at
            FROM zt_task
            WHERE estimate IS NOT NULL AND estimate > 0
        """)
        rows = cursor.fetchall()
        cursor.close()
        log.info(f"任务数据: {len(rows)} 条")
        return rows

    def fetch_bugs(self) -> List[Dict]:
        """抽取 Bug 数据"""
        cursor = self.conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT id, title, severity, priority, status, project_id,
                   assigned_to, created_by, created_at, resolved_at
            FROM zt_bug
        """)
        rows = cursor.fetchall()
        cursor.close()
        log.info(f"Bug 数据: {len(rows)} 条")
        return rows

    def fetch_projects(self) -> List[Dict]:
        """抽取项目数据 (含聚合统计)"""
        cursor = self.conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT p.*,
                   (SELECT COUNT(*) FROM zt_task t WHERE t.project_id=p.id) as task_total,
                   (SELECT COUNT(*) FROM zt_task t WHERE t.project_id=p.id AND t.status='done') as task_done,
                   (SELECT COUNT(*) FROM zt_bug b WHERE b.project_id=p.id) as bug_total,
                   (SELECT COUNT(*) FROM zt_bug b WHERE b.project_id=p.id AND b.status='resolved') as bug_resolved
            FROM zt_project p
        """)
        rows = cursor.fetchall()
        cursor.close()
        log.info(f"项目数据: {len(rows)} 条")
        return rows

    # ========== 特征工程 ==========

    def extract_bug_text_features(self, title: str) -> str:
        """提取 Bug 标题关键特征词"""
        keywords = {
            "fatal":   ["崩溃", "死机", "数据丢失", "安全漏洞", "资金", "越权", "注入"],
            "serious": ["超时", "白屏", "报错", "500", "无法", "异常", "错误", "失败"],
            "normal":  ["显示", "样式", "偏移", "乱码", "格式", "排列", "排序"],
            "minor":   ["拼写", "颜色", "间距", "提示", "文案", "建议"],
        }
        # 计算每个级别的特征词命中数
        features = []
        for level in ["fatal", "serious", "normal", "minor"]:
            hits = sum(1 for kw in keywords[level] if kw in title)
            features.append(str(hits))
        features.append(str(len(title)))
        features.append(str(1) if any(c.isascii() and not c.isalpha() for c in title) else str(0))
        return " ".join(features)

    def build_task_training_data(self, tasks: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """构建任务耗时预测训练数据"""
        X, y = [], []
        for t in tasks:
            consumed = t.get("consumed") or 0
            if consumed <= 0:
                continue
            estimate = t.get("estimate") or 0
            priority_map = {"high": 4, "medium": 3, "low": 2, "urgent": 5}
            priority_val = priority_map.get(t.get("priority", "medium"), 3)
            features = [
                estimate,
                priority_val,
                t.get("project_id") or 0,
                t.get("assigned_to") or 0,
            ]
            X.append(features)
            y.append(consumed)
        log.info(f"任务训练样本: {len(X)}")
        return np.array(X), np.array(y)

    def build_bug_training_data(self, bugs: List[Dict]) -> Tuple[List[str], np.ndarray, TfidfVectorizer]:
        """构建 Bug 严重度分类训练数据 — 返回原始文本列表和未拟合的 vectorizer"""
        texts = []
        labels = []
        for b in bugs:
            severity = b.get("severity", 3)
            title = b.get("title", "")
            if not title:
                continue
            text_features = self.extract_bug_text_features(title)
            texts.append(text_features)
            labels.append(severity)

        vectorizer = TfidfVectorizer(analyzer="word", ngram_range=(1, 2), max_features=100)
        # 不在这里 fit_transform，由调用方 Pipeline 或直接使用

        le = LabelEncoder()
        y = le.fit_transform(labels)
        self.label_encoders["bug_severity"] = le

        log.info(f"Bug 训练样本: {len(texts)}, 类别: {list(le.classes_)}")
        return texts, y, vectorizer

    def build_project_training_data(self, projects: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """构建项目风险预测训练数据"""
        X, y_labels = [], []
        for p in projects:
            task_total = int(p.get("task_total") or 0)
            task_done = int(p.get("task_done") or 0)
            bug_total = int(p.get("bug_total") or 0)
            bug_resolved = int(p.get("bug_resolved") or 0)

            if task_total == 0 and bug_total == 0:
                continue

            completion_rate = task_done / task_total if task_total > 0 else 0
            bug_rate = bug_resolved / bug_total if bug_total > 0 else 0

            features = [
                task_total, task_done, bug_total, bug_resolved,
                completion_rate, bug_rate,
            ]
            X.append(features)

            # 风险标签: low(0) medium(1) high(2) critical(3)
            health = completion_rate * 40 + bug_rate * 30
            if health >= 75:
                risk = 0
            elif health >= 50:
                risk = 1
            elif health >= 25:
                risk = 2
            else:
                risk = 3
            y_labels.append(risk)

        le = LabelEncoder()
        y = le.fit_transform(y_labels)
        self.label_encoders["project_risk"] = le

        log.info(f"项目训练样本: {len(X)}, 风险分布: {dict(zip(*np.unique(y, return_counts=True)))}")
        return np.array(X), y

    # ========== 模型训练 ==========

    def train_bug_severity_model(self, bugs: List[Dict]) -> Optional[Pipeline]:
        """训练 Bug 严重度分类器"""
        X, y, vectorizer = self.build_bug_training_data(bugs)
        if len(y) < 10 or len(np.unique(y)) < 2:
            log.warning("Bug 训练数据不足")
            # 创建规则后备模型
            return self._create_keyword_bug_model()

        clf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
        pipeline = Pipeline([("vectorizer", vectorizer), ("classifier", clf)])

        try:
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            pipeline.fit(X_train, y_train)
            y_pred = pipeline.predict(X_test)
            acc = accuracy_score(y_test, y_pred)
            log.info(f"Bug 严重度模型: accuracy={acc:.2%}")
        except Exception as e:
            log.warning(f"模型训练降级: {e}")
            pipeline.fit(X, y)

        self.models["bug_severity"] = pipeline

        # 保存模型
        with open(MODEL_DIR / "bug_severity_model.pkl", "wb") as f:
            pickle.dump(pipeline, f)
        with open(MODEL_DIR / "bug_severity_encoder.pkl", "wb") as f:
            pickle.dump(self.label_encoders["bug_severity"], f)

        return pipeline

    def _create_keyword_bug_model(self) -> Dict:
        """基于关键词的 Bug 严重度规则模型 (后备)"""
        rules = {
            "fatal":   ["崩溃", "死机", "数据丢失", "安全漏洞", "资金", "越权", "注入", "fatal"],
            "serious": ["超时", "白屏", "报错", "500", "无法", "异常", "错误", "失败", "serious"],
            "normal":  ["显示", "样式", "偏移", "乱码", "格式", "排列", "排序", "normal"],
            "minor":   ["拼写", "颜色", "间距", "提示", "文案", "建议", "minor"],
        }
        model = {"type": "keyword_rules", "rules": rules}
        self.models["bug_severity"] = model
        with open(MODEL_DIR / "bug_severity_model.pkl", "wb") as f:
            pickle.dump(model, f)
        log.info("Bug 严重度模型: 使用关键词规则 (数据不足)")
        return model

    def train_task_duration_model(self, tasks: List[Dict]) -> Optional[GradientBoostingRegressor]:
        """训练任务耗时预测回归器"""
        X, y = self.build_task_training_data(tasks)
        if len(y) < 10:
            log.warning("任务训练数据不足")
            return None

        model = GradientBoostingRegressor(
            n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42
        )

        try:
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            log.info(f"任务耗时模型: MAE={mae:.1f}h, R²={r2:.3f}")
        except Exception as e:
            log.warning(f"训练降级: {e}")
            model.fit(X, y)

        self.models["task_duration"] = model

        with open(MODEL_DIR / "task_duration_model.pkl", "wb") as f:
            pickle.dump(model, f)

        return model

    def train_project_risk_model(self, projects: List[Dict]) -> Optional[RandomForestClassifier]:
        """训练项目风险分类器"""
        X, y = self.build_project_training_data(projects)
        if len(y) < 5 or len(np.unique(y)) < 2:
            log.warning("项目训练数据不足")
            return None

        model = RandomForestClassifier(n_estimators=50, max_depth=6, random_state=42)
        model.fit(X, y)

        self.models["project_risk"] = model

        with open(MODEL_DIR / "project_risk_model.pkl", "wb") as f:
            pickle.dump(model, f)
        with open(MODEL_DIR / "project_risk_encoder.pkl", "wb") as f:
            pickle.dump(self.label_encoders["project_risk"], f)

        # 特征重要性
        feature_names = ["task_total", "task_done", "bug_total", "bug_resolved",
                         "completion_rate", "bug_resolve_rate"]
        importance = dict(zip(feature_names, model.feature_importances_))
        log.info(f"项目风险模型 特征重要性: {importance}")
        return model

    # ========== 全部训练 ==========

    def train_all(self) -> Dict:
        """训练全部模型"""
        log.info("=" * 50)
        log.info("=== 禅道 AI 模型训练开始 ===")
        log.info("=" * 50)

        stats = {
            "trained_at": datetime.now().isoformat(),
            "models": {},
        }

        # 1. Bug 严重度分类
        bugs = self.fetch_bugs()
        if bugs:
            self.train_bug_severity_model(bugs)
            stats["models"]["bug_severity"] = {"samples": len(bugs), "trained": True}

        # 2. 任务耗时预测
        tasks = self.fetch_tasks()
        if tasks:
            self.train_task_duration_model(tasks)
            stats["models"]["task_duration"] = {"samples": len(tasks),
                                                 "trained": "task_duration" in self.models}

        # 3. 项目风险评估
        projects = self.fetch_projects()
        if projects:
            self.train_project_risk_model(projects)
            stats["models"]["project_risk"] = {"samples": len(projects),
                                                "trained": "project_risk" in self.models}

        log.info("=" * 50)
        log.info(f"=== 训练完成: {stats} ===")

        # 保存元数据
        with open(MODEL_DIR / "model_metadata.json", "w") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        self.conn.close()
        return stats


if __name__ == "__main__":
    trainer = ZentaoAITrainer()
    result = trainer.train_all()
    print(json.dumps(result, ensure_ascii=False, indent=2))
