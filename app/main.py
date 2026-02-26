from fastapi import FastAPI

from app.models import user, task
from app.api.routes.users import router as users_router

app = FastAPI(title="SprintSync API")

app.include_router(users_router)


@app.get("/")
def root():
    return {"message": "SprintSync running"}