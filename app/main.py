from fastapi import FastAPI

from app.models import user, task

app = FastAPI(title="SprintSync API")


@app.get("/")
def root():
    return {"message": "SprintSync running"}