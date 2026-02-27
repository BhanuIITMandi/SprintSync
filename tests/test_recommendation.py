from fastapi.testclient import TestClient

def test_recommend_user_happy_path(client, auth_headers):
    # 1. Create a user with specific skills
    # (The /users/ endpoint allows skills)
    client.post("/users/", json={
        "email": "engineer@example.com", 
        "password": "password",
        "skills": "python, fastapi, docker"
    })
    
    # 2. Get recommendation for a matching task
    resp = client.post(
        "/tasks/recommend-user",
        json={
            "title": "Build a Dockerized FastAPI app",
            "description": "Need someone to set up the backend container."
        },
        headers=auth_headers
    )
    
    assert resp.status_code == 200
    data = resp.json()
    assert "recommended_user" in data
    rec_user = data["recommended_user"]
    assert "score" in rec_user
    assert "active_tasks" in rec_user
    assert "semantic_similarity" in rec_user
