from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User

REGISTER_PAYLOAD = {
    "full_name": "Rohan Kanaujia",
    "email": "Rohan@Example.com",
    "phone": "+91 98765 43210",
    "password": "SecurePass123",
}


def test_register_login_and_get_current_user(
    client: TestClient, db_session: Session
) -> None:
    register_response = client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)

    assert register_response.status_code == 201
    registered_user = register_response.json()
    assert registered_user["email"] == "rohan@example.com"
    assert registered_user["full_name"] == "Rohan Kanaujia"
    assert registered_user["phone"] == "+91 98765 43210"
    assert registered_user["nabo_score"] == 100
    assert "password" not in registered_user
    assert "password_hash" not in registered_user

    stored_user = db_session.scalar(select(User))
    assert stored_user is not None
    assert stored_user.password_hash != REGISTER_PAYLOAD["password"]
    assert stored_user.password_hash.startswith("$argon2")

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "ROHAN@example.com",
            "password": REGISTER_PAYLOAD["password"],
        },
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert token_data["token_type"] == "bearer"
    assert token_data["access_token"]
    assert token_data["expires_in"] == 1800

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token_data['access_token']}"},
    )
    assert me_response.status_code == 200
    assert me_response.json() == registered_user


def test_duplicate_email_is_rejected(client: TestClient) -> None:
    assert (
        client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD).status_code == 201
    )

    duplicate_response = client.post(
        "/api/v1/auth/register",
        json={**REGISTER_PAYLOAD, "email": "ROHAN@example.com"},
    )

    assert duplicate_response.status_code == 409
    assert duplicate_response.json() == {
        "detail": "An account with this email already exists"
    }


def test_invalid_registration_data_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={**REGISTER_PAYLOAD, "email": "not-an-email", "password": "weak"},
    )

    assert response.status_code == 422


def test_incorrect_password_is_rejected(client: TestClient) -> None:
    assert (
        client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD).status_code == 201
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": "Incorrect123"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect email or password"}


def test_me_requires_a_valid_bearer_token(client: TestClient) -> None:
    missing_response = client.get("/api/v1/auth/me")
    invalid_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert missing_response.status_code == 401
    assert invalid_response.status_code == 401
    assert missing_response.headers["www-authenticate"] == "Bearer"
