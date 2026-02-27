# SprintSync

> Lean internal tool for engineers to log work, track time, and get AI-powered planning help using Google Gemini.

## Architecture

```
SprintSync/
├── app/
│   ├── main.py                 # FastAPI entry point, router registration, middleware
│   ├── api/routes/
│   │   ├── auth.py             # POST /auth/login — JWT authentication
│   │   ├── users.py            # POST /users/ — registration + skills
│   │   ├── tasks.py            # CRUD + recommendation + assignment
│   │   ├── ai.py               # POST /ai/suggest — Gemini-powered suggestions
│   │   └── metrics.py          # GET /metrics — Prometheus-style JSON
│   ├── core/
│   │   ├── security.py         # Password hashing, JWT encode/decode, auth deps
│   │   └── middleware.py       # Structured request logging + metrics collection
│   ├── db/
│   │   └── session.py          # SQLAlchemy engine, session, Base
│   ├── models/
│   │   ├── user.py             # User ORM model (with skills)
│   │   └── task.py             # Task ORM model (with owner/assignee)
│   └── schemas/
│       ├── user.py             # Pydantic: UserCreate, UserOut
│       └── task.py             # Pydantic: TaskCreate, TaskUpdate, TaskOut
├── db/
│   ├── schema.sql              # DDL for users + tasks tables
│   └── seed.sql                # Demo data (5 diverse roles, 25 tasks)
├── Dockerfile                  # Python 3.11 slim image
├── docker-compose.yml          # App + Postgres with seed data
├── requirements.txt            # Python dependencies
└── .env                        # Environment variables
```

## Quick Start

### With Docker (recommended)

1. Add your `GOOGLE_API_KEY` to the `.env` file.
2. Build and run:
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
export GOOGLE_API_KEY=your-gemini-api-key
export USE_AI_STUB=false

uvicorn app.main:app --reload
```

## API Reference

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/auth/login` | — | Login, returns JWT |
| `POST` | `/users/` | — | Register new user (can include `skills`) |
| `POST` | `/tasks/` | ✅ | Create task (can set `assigned_to`) |
| `GET` | `/tasks/` | ✅ | List tasks (admin: all, user: own/assigned) |
| `PATCH` | `/tasks/{id}/status` | ✅ | Transition status |
| `POST` | `/tasks/recommend-user` | ✅ | **Semantic** AI recommendation for a task |
| `POST` | `/ai/suggest` | ✅ | Gemini-powered draft description / daily plan |
| `GET` | `/metrics` | — | Prometheus-style JSON metrics |

## Key Features

### 🤖 Semantic Task Recommendation
Uses **Gemini Text Embeddings** (`models/gemini-embedding-001`) to matching tasks to the best user.
- **Context-aware:** Matches "scalable pipeline" to "Data Engineer" even without keyword overlap.
- **Workload-aware:** Penalizes scores for users who are already overloaded with `TODO` or `IN_PROGRESS` tasks.

### 🧠 Gemini AI Integration
The planning features are powered by `gemini-1.5-flash`:
- **Draft Description:** Generate detailed tasks from a simple title.
- **Daily Plan:** Synthesize a coherent plan from your current task list.

### Status Transitions

```
TODO ──→ IN_PROGRESS ──→ DONE
 ↑                         │
 └─────────────────────────┘
```

## Observability

### Structured Logging

Every request produces a JSON log line to stdout:

```json
{"timestamp": "2025-02-27T14:42:00+0000", "method": "POST", "path": "/tasks/recommend-user", "userId": "1", "status_code": 200, "latency_ms": 1245.34}
```

## Demo Credentials

The database is seeded with 5 users with specific skills:

| Email | Password | Role / Skills |
|-------|----------|---------------|
| `user1@example.com` | `user1` | Data Science (Python, ML) |
| `user2@example.com` | `user2` | SDE (Java, Spring, React) |
| `user3@example.com` | `user3` | Data Engineering (Spark, SQL) |
| `user4@example.com` | `user4` | DevOps (AWS, K8s, Docker) |
| `user5@example.com` | `user5` | QA (Selenium, Cypress) |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | — | PostgreSQL connection string |
| `SECRET_KEY` | `super-secret-key` | JWT signing key |
| `USE_AI_STUB` | `true` | Use deterministic stubs instead of Gemini calls |
| `GOOGLE_API_KEY` | — | Google Gemini API key (Required for AI features) |

## Design Decisions

- **FastAPI** — async-ready, auto-generated OpenAPI docs.
- **Gemini Embeddings** — semantic similarity without needing a local vector database.
- **Workload Dampening** — recommendation logic considers current user bandwidth.
- **DB Seeding** — industry-standard roles to showcase the recommendation engine.