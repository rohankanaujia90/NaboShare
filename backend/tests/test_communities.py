import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import require_current_community
from app.models.community import Community
from app.models.user import User


def auth_headers(client: TestClient, email: str) -> dict[str, str]:
    password = "CommunityPass123"
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Community Member",
            "email": email,
            "password": password,
        },
    )
    assert register_response.status_code == 201
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_community_joins_creator(
    client: TestClient,
    db_session: Session,
) -> None:
    headers = auth_headers(client, "creator@example.com")

    response = client.post(
        "/api/v1/communities",
        headers=headers,
        json={
            "name": "  North Campus Residents  ",
            "type": "apartment_society",
            "city": "  Bengaluru  ",
        },
    )

    assert response.status_code == 201
    community = response.json()
    assert community["name"] == "North Campus Residents"
    assert community["type"] == "apartment_society"
    assert community["city"] == "Bengaluru"
    assert len(community["invite_code"]) == 8

    stored_user = db_session.scalar(
        select(User).where(User.email == "creator@example.com")
    )
    assert stored_user is not None
    assert str(stored_user.community_id) == community["id"]

    me_response = client.get("/api/v1/communities/me", headers=headers)
    assert me_response.status_code == 200
    assert me_response.json() == community


def test_user_can_join_with_case_insensitive_invite_code(
    client: TestClient,
    db_session: Session,
) -> None:
    creator_headers = auth_headers(client, "creator@example.com")
    created = client.post(
        "/api/v1/communities",
        headers=creator_headers,
        json={"name": "Tech Campus", "type": "corporate_campus", "city": "Pune"},
    ).json()
    member_headers = auth_headers(client, "member@example.com")

    join_response = client.post(
        "/api/v1/communities/join",
        headers=member_headers,
        json={"invite_code": created["invite_code"].lower()},
    )

    assert join_response.status_code == 200
    assert join_response.json()["id"] == created["id"]
    community = db_session.scalar(select(Community))
    assert community is not None
    assert {member.email for member in community.members} == {
        "creator@example.com",
        "member@example.com",
    }


def test_invalid_invite_code_is_rejected(client: TestClient) -> None:
    headers = auth_headers(client, "member@example.com")

    response = client.post(
        "/api/v1/communities/join",
        headers=headers,
        json={"invite_code": "NOTFOUND"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "No community was found for this invite code"}


def test_user_cannot_switch_communities(client: TestClient) -> None:
    first_headers = auth_headers(client, "first@example.com")
    first_community = client.post(
        "/api/v1/communities",
        headers=first_headers,
        json={"name": "First Hostel", "type": "hostel", "city": "Delhi"},
    ).json()
    second_headers = auth_headers(client, "second@example.com")
    second_response = client.post(
        "/api/v1/communities",
        headers=second_headers,
        json={"name": "Second College", "type": "college", "city": "Delhi"},
    )
    assert second_response.status_code == 201

    switch_response = client.post(
        "/api/v1/communities/join",
        headers=second_headers,
        json={"invite_code": first_community["invite_code"]},
    )

    assert switch_response.status_code == 409
    assert switch_response.json() == {
        "detail": "You already belong to a different community"
    }


def test_current_community_requires_auth_and_membership(client: TestClient) -> None:
    unauthorized_response = client.get("/api/v1/communities/me")
    headers = auth_headers(client, "unassigned@example.com")
    unassigned_response = client.get("/api/v1/communities/me", headers=headers)

    assert unauthorized_response.status_code == 401
    assert unassigned_response.status_code == 404
    assert unassigned_response.json() == {"detail": "You have not joined a community"}


def test_item_scope_is_derived_from_authenticated_users_community(
    client: TestClient,
    db_session: Session,
) -> None:
    headers = auth_headers(client, "scoped@example.com")
    created = client.post(
        "/api/v1/communities",
        headers=headers,
        json={"name": "Scoped Campus", "type": "college", "city": "Mumbai"},
    ).json()
    member = db_session.scalar(select(User).where(User.email == "scoped@example.com"))
    assert member is not None

    scope = require_current_community(current_user=member, db=db_session)

    assert str(scope.id) == created["id"]

    unassigned = User(
        full_name="No Community",
        email="none@example.com",
        password_hash="not-used",
    )
    db_session.add(unassigned)
    db_session.commit()
    with pytest.raises(HTTPException) as exc_info:
        require_current_community(current_user=unassigned, db=db_session)
    assert exc_info.value.status_code == 403
