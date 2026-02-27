import logging
import sys

from fastapi import FastAPI

from app.core.middleware import ObservabilityMiddleware
from app.api.routes.users import router as users_router
from app.api.routes.auth import router as auth_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.ai import router as ai_router
from app.api.routes.metrics import router as metrics_router

# ─── Structured logging setup ───
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    stream=sys.stdout,
)

app = FastAPI(
    title="SprintSync API",
    description="Lean internal tool for logging work, tracking time, and AI-powered planning.",
    version="1.0.0",
)

# ─── Middleware ───
app.add_middleware(ObservabilityMiddleware)

# ─── Routers ───
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(tasks_router)
app.include_router(ai_router)
app.include_router(metrics_router)


@app.get("/", tags=["Health"])
def root():
    return {"message": "SprintSync running", "docs": "/docs"}