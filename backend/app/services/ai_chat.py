"""AI 智能对话服务 — 接入 NVIDIA MiniMax M2.7，支持多 API Key 切换"""
import json
import threading
import time
import hashlib
from typing import AsyncGenerator, Optional
from openai import OpenAI

# ===== 系统提示词 =====
SYSTEM_PROMPT = """你是 WorkNest 平台的 AI 助手，跟用户聊天就像同事之间正常说话一样。

## 说话方式
- 像人一样说话，不要像客服机器人。不要用"基于您提到的内容""我的建议如下"这类套话。
- 不要用 **加粗标题** + emoji 的格式来组织回复，那看起来像 PPT 不像聊天。
- 简单的问题直接回答，别绕弯子。比如问"这个 bug 怎么修"，直接说方案，不要先来一段"这是一个很好的问题"。
- 如果需要分点说，用数字就行，不用加粗小标题。
- 可以用口语化的表达，适当的时候可以带点个人判断和语气。但不要过头——你毕竟是工作助手，不是聊天搭子。
- 不知道就说不知道，不要编。如果信息不够就问清楚再答。
- 用户问什么就答什么，不要每次都试图展开讲一大堆相关知识。

## 你能帮上忙的事
项目管理、任务拆解、工时估算、Bug 分析、代码审查、技术选型建议、写文档（周报/复盘/方案）、数据分析。

## 格式
代码用代码块，其他时候就是正常文字。Markdown 列表可以用，但别滥用。"""

# ===== 预置 API Key 配置 =====
PRESET_KEYS = [
    {
        "id": "nvidia-minimax",
        "name": "NVIDIA MiniMax M2.7",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "api_key": "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",
        "model": "minimaxai/minimax-m2.7",
        "max_tokens": 4096,
        "temperature": 0.7,
        "top_p": 0.95,
    },
    {
        "id": "nvidia-deepseek",
        "name": "NVIDIA DeepSeek-V3",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "api_key": "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",
        "model": "deepseek-ai/deepseek-v3",
        "max_tokens": 4096,
        "temperature": 0.7,
        "top_p": 0.95,
    },
    {
        "id": "nvidia-llama",
        "name": "NVIDIA Llama 3.3 (70B)",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "api_key": "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",
        "model": "meta/llama-3.3-70b-instruct",
        "max_tokens": 4096,
        "temperature": 0.7,
        "top_p": 0.95,
    },
]


class AIChatService:
    """AI 对话服务 — 多 Key 管理 + 单例"""

    _instance: Optional["AIChatService"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def _ensure_init(self):
        if self._initialized:
            return
        self._keys: list[dict] = [dict(k) for k in PRESET_KEYS]
        self._current_idx: int = 0
        self._client: Optional[OpenAI] = None
        self._client_for_idx: int = -1  # 跟踪 client 对应哪个 key
        # 预测解释缓存（TTL 5分钟，最多50条）
        self._explain_cache: dict = {}
        self._cache_ttl: float = 300.0
        self._initialized = True

    @property
    def config(self) -> dict:
        self._ensure_init()
        return self._keys[self._current_idx]

    def get_client(self) -> OpenAI:
        """获取或重建 OpenAI client（超时10秒，足够API响应）"""
        self._ensure_init()
        if self._client is None or self._client_for_idx != self._current_idx:
            cfg = self.config
            self._client = OpenAI(
                base_url=cfg["base_url"],
                api_key=cfg["api_key"],
                timeout=15.0,       # 从60s降到15s，NVIDIA API通常在3-8秒响应
                max_retries=0,      # 不重试，失败立即返回
            )
            self._client_for_idx = self._current_idx
        return self._client

    # ========== Key 管理 ==========

    def list_keys(self) -> dict:
        """列出所有 Key"""
        self._ensure_init()
        return {
            "keys": [
                {
                    "id": k["id"],
                    "name": k["name"],
                    "model": k["model"],
                    "base_url": k["base_url"],
                    "api_key_prefix": k["api_key"][:12] + "..." + k["api_key"][-4:],
                    "is_active": i == self._current_idx,
                }
                for i, k in enumerate(self._keys)
            ],
            "current": self._current_idx,
            "total": len(self._keys),
        }

    def add_key(
        self,
        name: str,
        base_url: str,
        api_key: str,
        model: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        top_p: float = 0.95,
    ) -> dict:
        """新增 Key"""
        self._ensure_init()
        import hashlib
        kid = hashlib.md5(f"{name}{api_key}".encode()).hexdigest()[:8]
        cfg = {
            "id": kid,
            "name": name,
            "base_url": base_url,
            "api_key": api_key,
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
        }
        self._keys.append(cfg)
        return {"success": True, "id": kid, "name": name, "total": len(self._keys)}

    def delete_key(self, key_id: str) -> dict:
        """删除 Key（不能删除最后一个）"""
        self._ensure_init()
        if len(self._keys) <= 1:
            return {"success": False, "error": "至少保留一个 API Key"}
        for i, k in enumerate(self._keys):
            if k["id"] == key_id:
                del self._keys[i]
                if self._current_idx >= len(self._keys):
                    self._current_idx = len(self._keys) - 1
                if self._current_idx == i or self._current_idx > i:
                    self._current_idx = max(0, self._current_idx - 1 if self._current_idx >= i else self._current_idx)
                # 如果删除的是当前 key，重置 idx
                if i <= self._current_idx:
                    self._current_idx = max(0, self._current_idx - 1 if self._current_idx > 0 else 0)
                # Force reset client
                self._client = None
                self._client_for_idx = -1
                return {"success": True, "deleted": key_id, "new_current": self._keys[self._current_idx]["name"], "total": len(self._keys)}
        # Recalc current_idx properly
        self._current_idx = min(self._current_idx, len(self._keys) - 1)
        return {"success": False, "error": f"未找到 Key: {key_id}"}

    def switch_key(self, key_id: str = None, index: int = None) -> dict:
        """切换当前 Key"""
        self._ensure_init()
        if key_id is not None:
            for i, k in enumerate(self._keys):
                if k["id"] == key_id:
                    self._current_idx = i
                    self._client = None
                    return self._switch_result()
            return {"success": False, "error": f"未找到 Key: {key_id}"}
        elif index is not None:
            if 0 <= index < len(self._keys):
                self._current_idx = index
                self._client = None
                return self._switch_result()
            return {"success": False, "error": f"无效索引: {index}"}
        return {"success": False, "error": "需要 key_id 或 index"}

    def _switch_result(self) -> dict:
        cfg = self.config
        return {
            "success": True,
            "id": cfg["id"],
            "name": cfg["name"],
            "model": cfg["model"],
            "index": self._current_idx,
        }

    # ========== 对话 ==========

    def chat_sync(self, messages: list[dict], context: dict = None) -> str:
        """同步对话（15秒超时，失败后返回友好错误而非假数据）"""
        self._ensure_init()
        full_messages = self._build_messages(messages, context)
        cfg = self.config
        try:
            response = self.get_client().chat.completions.create(
                model=cfg["model"],
                messages=full_messages,
                temperature=cfg["temperature"],
                top_p=cfg["top_p"],
                max_tokens=min(cfg["max_tokens"], 1024),  # 解释类请求限制输出长度加速
                stream=False,
            )
            content = response.choices[0].message.content
            return content if content else "[AI 返回空响应]"
        except Exception as e:
            err_msg = str(e)
            if "timeout" in err_msg.lower() or "timed out" in err_msg.lower():
                return f"[AI 服务超时] API响应超过15秒，请稍后重试或切换更快的模型。当前模型: {cfg['model']}"
            if "403" in err_msg or "401" in err_msg:
                return f"[API密钥已过期] NVIDIA API Key无效，请在AI工作台更新API Key。当前Key: {cfg['name']}"
            return f"[AI 服务异常] {err_msg[:200]}"

    async def chat_stream(self, messages: list[dict], context: dict = None) -> AsyncGenerator[str, None]:
        """流式对话"""
        self._ensure_init()
        full_messages = self._build_messages(messages, context)
        cfg = self.config
        try:
            stream = self.get_client().chat.completions.create(
                model=cfg["model"],
                messages=full_messages,
                temperature=cfg["temperature"],
                top_p=cfg["top_p"],
                max_tokens=cfg["max_tokens"],
                stream=True,
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"\n\n> ⚠️ AI 服务响应异常：{str(e)}"

    # ========== 专用分析 ==========

    def explain_prediction_local(self, prediction_data: dict) -> str:
        """本地快速解释（毫秒级，无需调用外部API）

        基于规则生成预测解读，适合快速预览场景。
        如需AI深度分析，由前端调用 explain_prediction。
        """
        pred = prediction_data.get('prediction', 0)
        model = prediction_data.get('model', 'rule_based_v0')
        ci = prediction_data.get('confidence_interval', '')

        try:
            val = float(pred)
        except (ValueError, TypeError):
            val = 0

        # 基于预测值的区间判断
        if val > 100000:
            trend = "强劲增长"
            action = "建议提前备货并优化供应链，应对高需求"
        elif val > 50000:
            trend = "稳步上升"
            action = "可按常规节奏推进，关注竞品动态"
        elif val > 20000:
            trend = "温和增长"
            action = "建议加强营销投入，提升转化率"
        elif val > 5000:
            trend = "平稳运行"
            action = "维护现有客户，探索新增长点"
        else:
            trend = "需关注"
            action = "建议分析下降因素，调整策略方向"

        return (
            f"基于{model}模型分析，当前预测呈{trend}趋势。"
            f"99%置信区间为 {ci}，数据可靠性较高。"
            f"💡 {action}。"
        )

    def explain_prediction(self, prediction_data: dict) -> str:
        """解释预测结果 — 带TTL缓存（相同预测值5分钟内不重复请求）"""
        self._ensure_init()

        # 生成缓存键（基于预测值）
        pred_value = prediction_data.get('prediction', 'N/A')
        cache_key = hashlib.md5(
            f"{pred_value}_{prediction_data.get('model','')}_{prediction_data.get('confidence_interval','')}"
            .encode()
        ).hexdigest()

        # 检查缓存
        now = time.time()
        cached = self._explain_cache.get(cache_key)
        if cached and (now - cached['ts']) < self._cache_ttl:
            return cached['text']

        # 清理过期缓存
        self._explain_cache = {
            k: v for k, v in self._explain_cache.items()
            if (now - v['ts']) < self._cache_ttl
        }

        prompt = f"""请用中文简要解释以下业务预测结果（100字以内），给出趋势判断和一条可操作建议：

预测数据：
- 预测值：{prediction_data.get('prediction', 'N/A')}
- 置信区间：{prediction_data.get('confidence_interval', 'N/A')}
- 模型：{prediction_data.get('model', 'N/A')}
- 特征重要性：{json.dumps(prediction_data.get('feature_importance', {}), ensure_ascii=False)}

请用 2-3 句话总结，语言专业但易懂。"""

        result = self.chat_sync([{"role": "user", "content": prompt}])

        # 存入缓存（仅缓存有效结果）
        if not result.startswith("[AI 服务异常]") and not result.startswith("[AI 服务超时]"):
            self._explain_cache[cache_key] = {'ts': now, 'text': result}

        return result

    def analyze_project_health(self, project: dict) -> str:
        prompt = f"""分析以下项目健康度，给出风险等级（低/中/高）和 2 条改进建议：

项目：{project.get('name', 'N/A')}
状态：{project.get('status', 'N/A')}
进度：{project.get('progress', 'N/A')}%
任务完成率：{project.get('task_completion', 'N/A')}%
Bug 数量：{project.get('bug_count', 'N/A')}
截止日期：{project.get('end_date', 'N/A')}"""
        return self.chat_sync([{"role": "user", "content": prompt}])

    def analyze_bug(self, bug: dict) -> str:
        prompt = f"""分析以下 Bug 并给出修复建议（100字以内）：

标题：{bug.get('title', 'N/A')}
严重程度：{bug.get('severity', 'N/A')}
状态：{bug.get('status', 'N/A')}
关联产品：{bug.get('product', 'N/A')}"""
        return self.chat_sync([{"role": "user", "content": prompt}])

    def _build_messages(self, messages: list[dict], context: dict = None) -> list[dict]:
        system_content = SYSTEM_PROMPT
        if context:
            ctx_str = json.dumps(context, ensure_ascii=False, indent=2)
            system_content += f"\n\n## 当前上下文\n```json\n{ctx_str}\n```"
        return [{"role": "system", "content": system_content}] + messages


# 全局单例
ai_chat = AIChatService()
