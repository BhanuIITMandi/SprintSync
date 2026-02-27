"""Integration test for the /ai/suggest endpoint (stub mode)."""


def test_ai_suggest_draft_description_stub(client, auth_headers):
    """POST /ai/suggest with mode=draft_description returns deterministic stub."""
    resp = client.post(
        "/ai/suggest",
        json={"mode": "draft_description", "title": "Login page"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "draft_description"
    assert data["source"] == "stub"
    assert "Login page" in data["suggestion"]
    assert "Acceptance Criteria" in data["suggestion"]


def test_ai_suggest_daily_plan_stub(client, auth_headers):
    """POST /ai/suggest with mode=daily_plan returns deterministic stub."""
    # Create a task first so the plan has content
    client.post(
        "/tasks/",
        json={"title": "Review PRs"},
        headers=auth_headers,
    )

    resp = client.post(
        "/ai/suggest",
        json={"mode": "daily_plan"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "daily_plan"
    assert data["source"] == "stub"
    assert "Daily Plan" in data["suggestion"] or "Review PRs" in data["suggestion"]
