import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure USE_AI_STUB is true for tests
os.environ["USE_AI_STUB"] = "true"
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-secret"

from app.db.session import Base, get_db
from app.main import app


# ─── In-memory SQLite engine for tests ───
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    """Create all tables before each test, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_token(client):
    """Register a user and return a valid JWT token."""
    client.post("/users/", json={"email": "testuser@example.com", "password": "testpass123"})
    
    # OAuth2PasswordRequestForm expects form-data with 'username' and 'password'
    login_resp = client.post(
        "/auth/login", 
        data={"username": "testuser@example.com", "password": "testpass123"}
    )
    
    if login_resp.status_code != 200:
        raise Exception(f"Login failed in test setup: {login_resp.text}")
        
    return login_resp.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}
