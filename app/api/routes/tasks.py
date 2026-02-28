from fastapi import APIRouter, Depends, HTTPException
import os
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import logging

from app.db.session import get_db
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskOut, TaskUpdate, TaskUpdateStatus
from app.core.security import get_current_user

logger = logging.getLogger("sprintsync")
router = APIRouter(prefix="/tasks", tags=["Tasks"])

VALID_TRANSITIONS = {
    "TODO": ["IN_PROGRESS"],
    "IN_PROGRESS": ["DONE", "TODO"],
    "DONE": ["TODO"],
}


@router.post("/", response_model=TaskOut)
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Default: assign to current user if not specified
    assignee_id = task.assigned_to if task.assigned_to is not None else current_user.id

    # Validate assignee exists
    if assignee_id != current_user.id:
        assignee = db.query(User).filter(User.id == assignee_id).first()
        if not assignee:
            raise HTTPException(status_code=404, detail=f"User with id {assignee_id} not found")

    new_task = Task(
        title=task.title,
        description=task.description,
        total_minutes=task.total_minutes or 0,
        user_id=current_user.id,
        assigned_to=assignee_id,
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task


@router.get("/", response_model=List[TaskOut])
def list_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.is_admin:
        return db.query(Task).all()
    return db.query(Task).filter(Task.user_id == current_user.id).all()


@router.get("/{task_id}", response_model=TaskOut)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not current_user.is_admin and task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorised")
    return task


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    updates: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not current_user.is_admin and task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorised")

    update_data = updates.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)

    db.commit()
    db.refresh(task)
    return task


@router.patch("/{task_id}/status", response_model=TaskOut)
def update_task_status(
    task_id: int,
    body: TaskUpdateStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not current_user.is_admin and task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorised")

    new_status = body.status.upper()
    allowed = VALID_TRANSITIONS.get(task.status, [])
    if new_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from {task.status} to {new_status}. Allowed: {allowed}",
        )

    task.status = new_status
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not current_user.is_admin and task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorised")

    db.delete(task)
    db.commit()
    return {"detail": "Task deleted"}


import google.generativeai as genai
import math

class RecommendRequest(BaseModel):
    title: str
    description: Optional[str] = ""


def cosine_similarity(v1, v2):
    dot_product = sum(a * b for a, b in zip(v1, v2))
    magnitude1 = math.sqrt(sum(a * a for a in v1))
    magnitude2 = math.sqrt(sum(b * b for b in v2))
    if not magnitude1 or not magnitude2:
        return 0.0
    return dot_product / (magnitude1 * magnitude2)


async def get_embedding(text: str):
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        # Fallback to 0 if key not set during recommendation to avoid crash
        return [0.0] * 768
    genai.configure(api_key=api_key)
    result = await genai.embed_content_async(
        model="models/gemini-embedding-001",
        content=text,
        task_type="retrieval_document"
    )
    return result['embedding']


@router.post("/recommend-user")
async def recommend_user(
    req: RecommendRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    users = db.query(User).all()
    if not users:
        raise HTTPException(status_code=404, detail="No users found")

    task_text = f"{req.title}: {req.description or ''}"
    try:
        task_vector = await get_embedding(task_text)
    except Exception as e:
        logger.warning(f"Embedding API failed: {e}. Falling back to keyword matching.")
        # Fallback to basic keyword matching if API fails
        task_words = set(task_text.lower().split())
        task_vector = None

    recommendations = []
    for user in users:
        # 1. Similarity Score
        if task_vector:
            user_skills = user.skills or "No skills listed"
            try:
                user_vector = await get_embedding(user_skills)
                similarity = cosine_similarity(task_vector, user_vector)
            except:
                similarity = 0.0
        else:
            # Fallback logic (keyword overlap)
            user_skills = (user.skills or "").lower()
            skill_words = set(user_skills.replace(",", " ").split())
            overlap = len(task_words.intersection(skill_words))
            similarity = overlap / (len(task_words) + 1)

        # 2. Workload Score (Active tasks)
        active_tasks = db.query(Task).filter(
            Task.assigned_to == user.id,
            Task.status.in_(["TODO", "IN_PROGRESS"])
        ).count()

        # 3. Final Score: Similarity penalized by workload
        # Adding 1 to active_tasks to dampen the effect
        score = similarity / (1 + active_tasks)

        recommendations.append({
            "user_id": user.id,
            "email": user.email,
            "skills": user.skills,
            "active_tasks": active_tasks,
            "score": score,
            "semantic_similarity": similarity
        })

    # Sort by score descending
    recommendations.sort(key=lambda x: x["score"], reverse=True)

    return {
        "recommended_user": recommendations[0] if recommendations else None,
        "all_scores": recommendations,
        "method": "semantic" if task_vector else "keyword_fallback"
    }
