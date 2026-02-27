# SprintSync

> Lean internal tool for engineers to log work, track time, and get AI-powered planning help.

## Architecture

```
SprintSync/
├── app/
│   ├── main.py                 # FastAPI entry point, router registration, middleware
│   ├── api/routes/
│   │   ├── auth.py             # POST /auth/login — JWT authentication
│   │   ├── users.py            # POST /users/ — user registration
│   │   ├── tasks.py            # CRUD + status transition for tasks
│   │   ├── ai.py               # POST /ai/suggest — LLM-powered suggestions
│   │   └── metrics.py          # GET /metrics — Prometheus-style JSON
│   ├── core/
│   │   ├── security.py         # Password hashing, JWT encode/decode, auth deps
│   │   └── middleware.py       # Structured request logging + metrics collection
│   ├── db/
│   │   └── session.py          # SQLAlchemy engine, session, Base
│   ├── models/
│   │   ├── user.py             # User ORM model
│   │   └── task.py             # Task ORM model
│   └── schemas/
│       ├── user.py             # Pydantic: UserCreate, UserOut
│       └── task.py             # Pydantic: TaskCreate, TaskUpdate, TaskOut, TaskUpdateStatus
├── db/
│   ├── schema.sql              # DDL for users + tasks tables
│   └── seed.sql                # Demo data (2 users, 5 tasks)
├── tests/
│   ├── conftest.py             # In-memory SQLite fixtures, test client
│   ├── test_users.py           # User registration tests
│   ├── test_tasks.py           # Task CRUD + status transition tests
│   └── test_ai.py              # AI suggest integration tests (stub mode)
├── Dockerfile                  # Python 3.11 slim image
├── docker-compose.yml          # App + Postgres with seed data
├── requirements.txt            # Python dependencies
└── .env                        # Environment variables
```

## Quick Start

### With Docker (recommended)

```bash
docker-compose up --build
```

API available at **http://localhost:8000** · Swagger docs at **http://localhost:8000/docs**

### Without Docker

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL=postgresql://postgres:password@localhost:5432/sprintsync
export SECRET_KEY=your-secret-key
export USE_AI_STUB=true

uvicorn app.main:app --reload
```

## API Reference

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/auth/login` | — | Login, returns JWT |
| `POST` | `/users/` | — | Register new user |
| `POST` | `/tasks/` | ✅ | Create task |
| `GET` | `/tasks/` | ✅ | List tasks (admin: all, user: own) |
| `GET` | `/tasks/{id}` | ✅ | Get single task |
| `PATCH` | `/tasks/{id}` | ✅ | Update task fields |
| `PATCH` | `/tasks/{id}/status` | ✅ | Transition status |
| `DELETE` | `/tasks/{id}` | ✅ | Delete task |
| `POST` | `/ai/suggest` | ✅ | AI draft description / daily plan |
| `GET` | `/metrics` | — | Prometheus-style JSON metrics |
| `GET` | `/docs` | — | Swagger UI |
| `GET` | `/redoc` | — | ReDoc |

### Status Transitions

```
TODO ──→ IN_PROGRESS ──→ DONE
 ↑                         │
 └─────────────────────────┘
```

Allowed: `TODO→IN_PROGRESS`, `IN_PROGRESS→DONE`, `IN_PROGRESS→TODO`, `DONE→TODO`

### AI Suggest Modes

**`draft_description`** — generates a task description from a short title:
```json
POST /ai/suggest
{"mode": "draft_description", "title": "Login page"}
```

**`daily_plan`** — generates a daily plan from the user's tasks:
```json
POST /ai/suggest
{"mode": "daily_plan"}
```

Set `USE_AI_STUB=true` or omit `OPENAI_API_KEY` to use deterministic stubs (CI-safe).

## Observability

### Structured Logging

Every request produces a JSON log line to stdout:

```json
{"timestamp": "2025-01-15T10:30:00+0530", "method": "GET", "path": "/tasks/", "userId": "1", "status_code": 200, "latency_ms": 12.34}
```

5xx errors include a `stacktrace` field.

### Metrics

`GET /metrics` returns:

```json
{
  "http_requests_total": [{"method": "GET", "path": "/tasks/", "status": 200, "count": 42}],
  "http_request_duration_seconds_bucket": {"le_0.01": 30, "le_0.05": 40, ...},
  "active_users": 2,
  "tasks_by_status": {"TODO": 2, "IN_PROGRESS": 1, "DONE": 2}
}
```

## Testing

```bash
pip install -r requirements.txt
USE_AI_STUB=true DATABASE_URL=sqlite:// pytest tests/ -v
```

Tests run against an in-memory SQLite database — no Docker or Postgres required.

| Test File | Tests | What it covers |
|-----------|-------|----------------|
| `test_users.py` | 2 | Registration happy path, duplicate email |
| `test_tasks.py` | 2 | Task creation, status transition |
| `test_ai.py` | 2 | AI suggest stub (draft + daily plan) |

## Demo Credentials

| Email | Password | Role |
|-------|----------|------|
| `admin@sprintsync.io` | `password123` | Admin |
| `alice@sprintsync.io` | `password123` | User |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | — | PostgreSQL connection string |
| `SECRET_KEY` | `super-secret-key` | JWT signing key |
| `USE_AI_STUB` | `true` | Use deterministic AI stubs |
| `OPENAI_API_KEY` | — | OpenAI API key (optional) |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | Custom LLM endpoint |
| `OPENAI_MODEL` | `gpt-3.5-turbo` | Model name |

## Design Decisions

- **FastAPI** — async-ready, auto-generated OpenAPI docs, Pydantic validation.
- **SQLAlchemy ORM** — clean data modelling with relationship support.
- **JWT (python-jose)** — stateless auth, easy to scale horizontally.
- **Graceful AI degradation** — stub fallback ensures CI never needs a live API key.
- **In-memory SQLite for tests** — fast, isolated, no external dependencies.
- **Prometheus-style JSON metrics** — lightweight, no extra infra required.