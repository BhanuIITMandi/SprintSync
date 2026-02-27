#!/bin/bash
set -e

echo "Starting database initialization..."
python scripts/setup_db.py

echo "Starting SprintSync API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
