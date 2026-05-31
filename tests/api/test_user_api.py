import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from database.connection import Base, get_db


@pytest.fixture()
def test_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    yield

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(test_db):
    with TestClient(app) as test_client:
        yield test_client


def test_create_user(client):
    response = client.post(
        "/api/users/",
        json={"username": "andrei"},
    )

    assert response.status_code == 200

    data = response.json()

    assert "id" in data
    assert data["username"] == "andrei"
    assert "created_at" in data


def test_create_same_user_returns_existing_user(client):
    first_response = client.post(
        "/api/users/",
        json={"username": "andrei"},
    )

    second_response = client.post(
        "/api/users/",
        json={"username": "andrei"},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    first_user = first_response.json()
    second_user = second_response.json()

    assert first_user["id"] == second_user["id"]
    assert first_user["username"] == second_user["username"]


def test_create_user_trims_username(client):
    response = client.post(
        "/api/users/",
        json={"username": "  andrei  "},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["username"] == "andrei"


def test_create_user_rejects_blank_username(client):
    response = client.post(
        "/api/users/",
        json={"username": "   "},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Username cannot be empty."


def test_create_user_rejects_missing_username(client):
    response = client.post(
        "/api/users/",
        json={},
    )

    assert response.status_code == 422


def test_get_user_by_id(client):
    create_response = client.post(
        "/api/users/",
        json={"username": "andrei"},
    )

    assert create_response.status_code == 200

    created_user = create_response.json()

    response = client.get(f"/api/users/{created_user['id']}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == created_user["id"]
    assert data["username"] == "andrei"
    assert "created_at" in data


def test_get_user_not_found(client):
    response = client.get("/api/users/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found."


def test_get_users_empty(client):
    response = client.get("/api/users/")

    assert response.status_code == 200
    assert response.json() == {"users": []}


def test_get_users_after_creating_users(client):
    client.post("/api/users/", json={"username": "maria"})
    client.post("/api/users/", json={"username": "andrei"})

    response = client.get("/api/users/")

    assert response.status_code == 200

    data = response.json()

    assert "users" in data
    assert len(data["users"]) == 2

    usernames = [user["username"] for user in data["users"]]

    assert usernames == ["andrei", "maria"]