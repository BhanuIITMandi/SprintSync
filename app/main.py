from fastapi import FastAPI

app = FastAPI(title="SprintSync API")


@app.get("/")
def root():
    return {"message": "SprintSync running"}