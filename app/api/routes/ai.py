import os
import json
import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal
from sqlalchemy.orm import Session
import google.generativeai as genai

from app.db.session import get_db
from app.models.task import Task
from app.models.user import User
from app.core.security import get_current_user

logger = logging.getLogger("sprintsync")

router = APIRouter(prefix="/ai", tags=["AI Assist"])


class AISuggestRequest(BaseModel):
    mode: Literal["draft_description", "daily_plan"]
    title: Optional[str] = None


class AISuggestResponse(BaseModel):
    mode: str
    suggestion: str
    source: str  # "live" or "stub"


# --------------- deterministic stubs ---------------

def _stub_draft_description(title: str) -> str:
    return (
        f"## {title}\n\n"
        f"**Objective**: Implement the '{title}' feature.\n\n"
        f"**Acceptance Criteria**:\n"
        f"- [ ] Core functionality is implemented and tested\n"
        f"- [ ] Edge cases are handled gracefully\n"
        f"- [ ] Code reviewed and documented\n\n"
        f"**Estimated effort**: 2–4 hours"
    )


def _stub_daily_plan(user: User, tasks: list[Task]) -> str:
    todo = [t for t in tasks if t.status == "TODO"]
    in_progress = [t for t in tasks if t.status == "IN_PROGRESS"]

    lines = [f"# Daily Plan — {date.today().isoformat()}\n"]

    if in_progress:
        lines.append("## 🔄 Continue In-Progress")
        for t in in_progress:
            lines.append(f"- **{t.title}** ({t.total_minutes} min logged)")

    if todo:
        lines.append("\n## 📋 Pick Up Next")
        for t in todo[:3]:
            lines.append(f"- {t.title}")

    if not todo and not in_progress:
        lines.append("🎉 All caught up! No pending tasks.")

    return "\n".join(lines)


# --------------- live LLM call ---------------

def _get_gemini_model():
    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not set")
    genai.configure(api_key=api_key)
    # Using 'gemini-2.0-flash' which is verified as available
    return genai.GenerativeModel('gemini-2.0-flash')


async def _llm_draft_description(title: str) -> str:
    """Call Gemini API to draft a task description."""
    model = _get_gemini_model()
    
    prompt = (
        "You are a concise project-management assistant. "
        f"Draft a clear task description for: {title}. "
        "Include objective, acceptance criteria, and estimated effort."
    )
    
    response = await model.generate_content_async(prompt)
    return response.text


async def _llm_daily_plan(user: User, tasks: list[Task]) -> str:
    """Call Gemini API to generate a daily plan."""
    model = _get_gemini_model()

    task_summary = "\n".join(
        f"- {t.title} [status={t.status}, minutes={t.total_minutes}]"
        for t in tasks
    )

    prompt = (
        "You are a concise project-management assistant. "
        "Given the following list of tasks, create a focused daily plan "
        "prioritising in-progress work, then TODO items.\n\n"
        f"Tasks:\n{task_summary}"
    )

    response = await model.generate_content_async(prompt)
    return response.text


# --------------- endpoint ---------------

def _use_stub() -> bool:
    """Return True when we should use the deterministic stub."""
    if os.getenv("USE_AI_STUB", "").lower() in ("true", "1", "yes"):
        return True
    if not os.getenv("GOOGLE_API_KEY"):
        return True
    return False


@router.post("/suggest", response_model=AISuggestResponse)
async def ai_suggest(
    body: AISuggestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    use_stub = _use_stub()

    if body.mode == "draft_description":
        if not body.title:
            raise HTTPException(status_code=400, detail="title is required for draft_description mode")

        if use_stub:
            suggestion = _stub_draft_description(body.title)
            source = "stub"
        else:
            try:
                suggestion = await _llm_draft_description(body.title)
                source = "live"
            except Exception as exc:
                logger.warning("LLM call failed, falling back to stub: %s", exc)
                suggestion = _stub_draft_description(body.title)
                source = "stub"

    elif body.mode == "daily_plan":
        tasks = db.query(Task).filter(Task.user_id == current_user.id).all()

        if use_stub:
            suggestion = _stub_daily_plan(current_user, tasks)
            source = "stub"
        else:
            try:
                suggestion = await _llm_daily_plan(current_user, tasks)
                source = "live"
            except Exception as exc:
                logger.warning("LLM call failed, falling back to stub: %s", exc)
                suggestion = _stub_daily_plan(current_user, tasks)
                source = "stub"

    else:
        raise HTTPException(status_code=400, detail="Invalid mode")

    return AISuggestResponse(mode=body.mode, suggestion=suggestion, source=source)
