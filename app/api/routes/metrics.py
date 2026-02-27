from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from collections import defaultdict

from app.db.session import get_db
from app.models.task import Task
from app.models.user import User
from app.core.middleware import get_metrics_store

router = APIRouter(tags=["Metrics"])


@router.get("/metrics")
def metrics(db: Session = Depends(get_db)):
    store = get_metrics_store()

    # ── HTTP request counters ──
    requests_total = []
    for (method, path, status), count in store["http_requests_total"].items():
        requests_total.append({
            "method": method,
            "path": path,
            "status": status,
            "count": count,
        })

    # ── Duration histogram (simplified buckets) ──
    durations = store["http_request_duration_seconds"]
    buckets = {"le_0.01": 0, "le_0.05": 0, "le_0.1": 0, "le_0.5": 0, "le_1": 0, "le_inf": 0}
    for _, _, d in durations:
        if d <= 0.01:
            buckets["le_0.01"] += 1
        if d <= 0.05:
            buckets["le_0.05"] += 1
        if d <= 0.1:
            buckets["le_0.1"] += 1
        if d <= 0.5:
            buckets["le_0.5"] += 1
        if d <= 1.0:
            buckets["le_1"] += 1
        buckets["le_inf"] += 1

    # ── App-level metrics from DB ──
    active_users = db.query(User).count()

    tasks_by_status = {}
    for status, count in db.query(Task.status, db.query(Task).with_entities(Task.status).correlate(None).count()).group_by(Task.status).all():
        tasks_by_status[status] = count

    # safer query
    from sqlalchemy import func
    tasks_by_status = {}
    for row in db.query(Task.status, func.count(Task.id)).group_by(Task.status).all():
        tasks_by_status[row[0]] = row[1]

    return {
        "http_requests_total": requests_total,
        "http_request_duration_seconds_bucket": buckets,
        "http_request_duration_seconds_count": len(durations),
        "http_request_duration_seconds_sum": round(sum(d for _, _, d in durations), 4),
        "active_users": active_users,
        "tasks_by_status": tasks_by_status,
    }
