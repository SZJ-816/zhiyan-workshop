"""AI 智能对话 API — 基于禅道系统真实数据"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from .auth import get_current_user
from app.services.ai_chat import ai_chat
from ai_model.inference.zentao_predictor import predictor
import json

router = APIRouter(prefix="/api/ai", tags=["AI助手"])


class ChatRequest(BaseModel):
    messages: list[dict]
    context: Optional[dict] = None
    stream: bool = False


class BugPredictRequest(BaseModel):
    title: str


class TaskPredictRequest(BaseModel):
    estimate: float = 8
    priority: str = "medium"
    project_id: int = 1
    assigned_to: int = 1


class ProjectAnalysisRequest(BaseModel):
    project_id: int


class BugAnalysisRequest(BaseModel):
    bug: dict


class AddKeyRequest(BaseModel):
    name: str
    base_url: str
    api_key: str
    model: str
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 0.95


class SwitchKeyRequest(BaseModel):
    key_id: Optional[str] = None
    index: Optional[int] = None


# ========== API Key 管理 ==========

@router.get("/keys")
async def list_keys(user=Depends(get_current_user)):
    return ai_chat.list_keys()


@router.post("/keys/add")
async def add_key(req: AddKeyRequest, user=Depends(get_current_user)):
    return ai_chat.add_key(
        name=req.name, base_url=req.base_url, api_key=req.api_key,
        model=req.model, max_tokens=req.max_tokens,
        temperature=req.temperature, top_p=req.top_p,
    )


@router.delete("/keys/{key_id}")
async def delete_key(key_id: str, user=Depends(get_current_user)):
    result = ai_chat.delete_key(key_id)
    if not result["success"]:
        raise HTTPException(400, result["error"])
    return result


@router.post("/keys/switch")
async def switch_key(req: SwitchKeyRequest, user=Depends(get_current_user)):
    result = ai_chat.switch_key(key_id=req.key_id, index=req.index)
    if not result["success"]:
        raise HTTPException(400, result["error"])
    return result


# ========== AI 对话 ==========

@router.post("/chat")
async def chat(req: ChatRequest, user=Depends(get_current_user)):
    if not req.messages:
        raise HTTPException(400, "messages 不能为空")
    reply = ai_chat.chat_sync(req.messages, req.context)
    return {"reply": reply, "model": "minimax-m2.7"}


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest, user=Depends(get_current_user)):
    if not req.messages:
        raise HTTPException(400, "messages 不能为空")

    async def generate():
        async for token in ai_chat.chat_stream(req.messages, req.context):
            yield f"data: {json.dumps({'token': token})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ========== AI 预测解读 (真实禅道数据) ==========

@router.post("/explain-prediction")
async def explain_prediction(req: BugPredictRequest, user=Depends(get_current_user)):
    """AI 解读 Bug 严重度预测结果"""
    result = predictor.predict_bug_severity(req.title)

    explanation = ai_chat.chat_sync([{
        "role": "user",
        "content": f"请用一段话（不超过80字）分析这个Bug预测结果：Bug标题为「{req.title}」，预测严重度为{result['severity']}，置信度{result['confidence']}。给出修复优先级建议。"
    }])

    return {
        "prediction": result,
        "ai_explanation": explanation,
        "explanation_mode": "local",
    }


@router.post("/analyze-project")
async def analyze_project(req: ProjectAnalysisRequest, user=Depends(get_current_user)):
    """AI 项目风险分析"""
    risk = predictor.predict_project_risk(req.project_id)
    analysis = ai_chat.chat_sync([{
        "role": "user",
        "content": f"请分析这个项目的健康状况并提供改进建议（不超过100字）：\n"
                   f"项目: {risk.get('project_name')}, 风险等级: {risk.get('risk_level')}, "
                   f"健康分: {risk.get('health_score')}/100, 任务完成率: {risk.get('completion_rate')}%, "
                   f"Bug解决率: {risk.get('bug_resolve_rate')}%, "
                   f"风险因素: {risk.get('risk_factors', [])}"
    }])
    return {"risk_analysis": risk, "ai_advice": analysis}


@router.post("/analyze-bug")
async def analyze_bug(req: BugAnalysisRequest, user=Depends(get_current_user)):
    """AI Bug 修复建议"""
    bug = req.bug
    severity = bug.get("severity", "normal")
    title = bug.get("title", "")
    result = predictor.predict_bug_severity(title)

    analysis = ai_chat.chat_sync([{
        "role": "user",
        "content": f"请根据以下Bug信息给出2-3条具体修复建议（不超过100字）：\n"
                   f"标题: {title}, 严重度: {severity}, 模型预测: {result['severity']}"
    }])
    return {"prediction": result, "analysis": analysis}


@router.get("/dashboard-insights")
async def dashboard_insights(user=Depends(get_current_user)):
    """AI 仪表盘智能洞察"""
    from app.core.database import SessionLocal
    from app.models.models import Project, Task, Bug

    db = SessionLocal()
    try:
        total_projects = db.query(Project).count()
        total_tasks = db.query(Task).count()
        total_bugs = db.query(Bug).count()
        done_tasks = db.query(Task).filter(Task.status == "done").count()
        active_bugs = db.query(Bug).filter(Bug.status == "active").count()

        context = {
            "总项目数": total_projects, "总任务数": total_tasks,
            "已完成任务": done_tasks,
            "任务完成率": f"{round(done_tasks/total_tasks*100, 1)}%" if total_tasks else "0%",
            "总Bug数": total_bugs, "未解决Bug": active_bugs,
        }

        prompt = "请根据以上数据生成 3 条简短的工作建议（每条不超过40字），包括：风险预警、优化方向、本周关注重点。"
        reply = ai_chat.chat_sync([{"role": "user", "content": prompt}], context)
        return {"context": context, "insights": reply}
    finally:
        db.close()
