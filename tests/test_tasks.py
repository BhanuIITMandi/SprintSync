"""Unit tests for task endpoints."""


def test_create_task_happy_path(client, auth_headers):
    """Creating a task returns correct title and default status TODO."""
    resp = client.post(
        "/tasks/",
        json={"title": "Write unit tests", "description": "Cover happy paths"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Write unit tests"
    assert data["status"] == "TODO"
    assert data["total_minutes"] == 0


def test_status_transition_todo_to_in_progress(client, auth_headers):
    """Transitioning a task from TODO to IN_PROGRESS succeeds."""
    # Create task
    create_resp = client.post(
        "/tasks/",
        json={"title": "Design API"},
        headers=auth_headers,
    )
    task_id = create_resp.json()["id"]

    # Transition status
    resp = client.patch(
        f"/tasks/{task_id}/status",
        json={"status": "IN_PROGRESS"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "IN_PROGRESS"
