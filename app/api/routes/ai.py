import os
import json
import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal
from sqlalchemy.orm import Session

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

async def _llm_draft_description(title: str) -> str:
    """Call OpenAI-compatible API to draft a task description."""
    import httpx

    api_key = os.getenv("OPENAI_API_KEY", "")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a concise project-management assistant. "
                                   "Given a short task title, produce a clear task description "
                                   "with objective, acceptance criteria, and estimated effort.",
                    },
                    {"role": "user", "content": f"Draft a task description for: {title}"},
                ],
                "max_tokens": 300,
                "temperature": 0.7,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def _llm_daily_plan(user: User, tasks: list[Task]) -> str:
    """Call OpenAI-compatible API to generate a daily plan."""
    import httpx

    api_key = os.getenv("OPENAI_API_KEY", "")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    task_summary = "\n".join(
        f"- {t.title} [status={t.status}, minutes={t.total_minutes}]"
        for t in tasks
    )

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a concise project-management assistant. "
                                   "Given a list of tasks, create a focused daily plan "
                                   "prioritising in-progress work, then TODO items.",
                    },
                    {
                        "role": "user",
                        "content": f"Create a daily plan for these tasks:\n{task_summary}",
                    },
                ],
                "max_tokens": 400,
                "temperature": 0.7,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


# --------------- endpoint ---------------

def _use_stub() -> bool:
    """Return True when we should use the deterministic stub."""
    if os.getenv("USE_AI_STUB", "").lower() in ("true", "1", "yes"):
        return True
    if not os.getenv("OPENAI_API_KEY"):
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
