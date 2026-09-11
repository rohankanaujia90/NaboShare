import uuid
from datetime import date, timedelta
from decimal import Decimal
from itertools import product
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.community import Community
from app.models.item import Item
from app.models.user import User
from app.services import rental as service
from app.services.scoring import apply_score_event, score_label

TODAY = date(2030, 1, 10)


@pytest.mark.parametrize(
    ("score", "label"),
    [
        (100, "Excellent"),
        (90, "Excellent"),
        (89, "Good"),
        (75, "Good"),
        (74, "Average"),
        (60, "Average"),
        (59, "Risky"),
        (0, "Risky"),
    ],
)
def test_score_labels(score: int, label: str) -> None:
    assert score_label(score) == label


def test_overdue_active_blocks_next_pickup(
    client: TestClient, rental_setup: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    first = request(client, rental_setup, start=0, end=1).json()
    second = request(client, rental_setup, role="peer", start=1, end=2).json()
    assert action(client, rental_setup, first["id"], "accept").status_code == 200
    assert action(client, rental_setup, second["id"], "accept").status_code == 200
    assert action(client, rental_setup, first["id"], "start").status_code == 200
    monkeypatch.setattr(service, "today_utc", lambda: TODAY + timedelta(days=1))
    assert action(client, rental_setup, second["id"], "start").status_code == 409
    assert action(client, rental_setup, first["id"], "return").status_code == 200
    assert action(client, rental_setup, second["id"], "start").status_code == 200


@pytest.fixture
def rental_setup(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> dict[str, Any]:
    monkeypatch.setattr(service, "today_utc", lambda: TODAY)
    first = Community(
        name="Campus A", type="college", city="Delhi", invite_code="CAMPUSAA"
    )
    other = Community(
        name="Campus B", type="college", city="Delhi", invite_code="CAMPUSBB"
    )
    db_session.add_all([first, other])
    db_session.flush()
    users = {}
    for role in ("owner", "borrower", "peer", "stranger", "outsider", "unassigned"):
        community_id = (
            other.id
            if role == "outsider"
            else None
            if role == "unassigned"
            else first.id
        )
        user = User(
            full_name=role,
            email=f"{role}@example.com",
            password_hash="unused",
            community_id=community_id,
        )
        db_session.add(user)
        users[role] = user
    db_session.flush()
    item = Item(
        owner_id=users["owner"].id,
        community_id=first.id,
        title="Projector",
        description="Projector and cables",
        category="Electronics",
        rental_price_per_day=Decimal("150.55"),
        security_deposit=Decimal("1000"),
        replacement_value=Decimal("12000"),
        availability=True,
    )
    db_session.add(item)
    db_session.commit()
    headers = {
        role: {"Authorization": f"Bearer {create_access_token(user.id)[0]}"}
        for role, user in users.items()
    }
    return {"users": users, "headers": headers, "item": item, "community": first}


def request(
    client: TestClient,
    setup: dict[str, Any],
    role: str = "borrower",
    start: int = 1,
    end: int = 3,
) -> Any:
    return client.post(
        "/api/v1/rentals",
        headers=setup["headers"][role],
        json={
            "item_id": str(setup["item"].id),
            "start_date": str(TODAY + timedelta(days=start)),
            "end_date": str(TODAY + timedelta(days=end)),
        },
    )


def action(
    client: TestClient,
    setup: dict[str, Any],
    rental_id: str,
    verb: str,
    role: str = "owner",
) -> Any:
    return client.post(
        f"/api/v1/rentals/{rental_id}/{verb}", headers=setup["headers"][role]
    )


@pytest.mark.parametrize(
    ("price", "days", "amount", "fee"),
    [
        ("150.55", 2, "301.10", "30.11"),
        ("0.05", 1, "0.05", "0.01"),
        ("0", 10, "0.00", "0.00"),
        ("9999999999.99", 365, "3649999999996.35", "364999999999.64"),
    ],
)
def test_decimal_pricing(price: str, days: int, amount: str, fee: str) -> None:
    assert service.calculate_amounts(
        TODAY, TODAY + timedelta(days=days), Decimal(price)
    ) == (Decimal(amount), Decimal(fee))


@pytest.mark.parametrize("days", [0, -1])
def test_invalid_duration(days: int) -> None:
    with pytest.raises(service.RentalError):
        service.calculate_amounts(TODAY, TODAY + timedelta(days=days), Decimal("100"))


# Exhaustively check all six states, five actions, and both participant roles.
@pytest.mark.parametrize(
    ("state", "verb", "owner"),
    list(
        product(
            ["PENDING", "ACCEPTED", "REJECTED", "ACTIVE", "RETURNED", "CANCELLED"],
            ["accept", "reject", "cancel", "start", "return"],
            [True, False],
        )
    ),
)
def test_transition_matrix(state: str, verb: str, owner: bool) -> None:
    allowed = {
        ("PENDING", "accept"): "ACCEPTED",
        ("PENDING", "reject"): "REJECTED",
        ("PENDING", "cancel"): "CANCELLED",
        ("ACCEPTED", "cancel"): "CANCELLED",
        ("ACCEPTED", "start"): "ACTIVE",
        ("ACTIVE", "return"): "RETURNED",
    }
    if (state, verb) in allowed and (owner or verb == "cancel"):
        assert service.next_status(state, verb, owner) == allowed[(state, verb)]
    else:
        with pytest.raises(service.RentalError):
            service.next_status(state, verb, owner)


def test_full_lifecycle_and_snapshot(
    client: TestClient,
    rental_setup: dict[str, Any],
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = request(client, rental_setup)
    assert response.status_code == 201
    rental = response.json()
    assert rental["rental_amount"] == "301.10"
    assert rental["platform_fee"] == "30.11"
    assert rental["security_deposit"] == "1000.00"
    assert rental["status"] == "PENDING"
    rental_setup["item"].rental_price_per_day = Decimal("999")
    rental_setup["item"].security_deposit = Decimal("99")
    db_session.commit()
    accepted = action(client, rental_setup, rental["id"], "accept")
    assert accepted.status_code == 200
    assert accepted.json()["rental_amount"] == "301.10"
    assert accepted.json()["security_deposit"] == "1000.00"
    assert action(client, rental_setup, rental["id"], "start").status_code == 409
    monkeypatch.setattr(service, "today_utc", lambda: TODAY + timedelta(days=1))
    assert (
        action(client, rental_setup, rental["id"], "start").json()["status"] == "ACTIVE"
    )
    assert action(client, rental_setup, rental["id"], "cancel").status_code == 409
    assert (
        action(client, rental_setup, rental["id"], "return").json()["status"]
        == "RETURNED"
    )
    assert action(client, rental_setup, rental["id"], "accept").status_code == 409
    assert (
        client.delete(
            f"/api/v1/items/{rental['item_id']}",
            headers=rental_setup["headers"]["owner"],
        ).status_code
        == 409
    )


@pytest.mark.parametrize(
    ("role", "expected"), [("owner", 409), ("outsider", 404), ("unassigned", 403)]
)
def test_request_permissions(
    client: TestClient, rental_setup: dict[str, Any], role: str, expected: int
) -> None:
    assert request(client, rental_setup, role=role).status_code == expected


@pytest.mark.parametrize(("start", "end"), [(-1, 2), (2, 2), (3, 2), (1, 367)])
def test_invalid_request_dates(
    client: TestClient, rental_setup: dict[str, Any], start: int, end: int
) -> None:
    assert request(client, rental_setup, start=start, end=end).status_code == 422


def test_unavailable_and_duplicate_requests(
    client: TestClient, rental_setup: dict[str, Any], db_session: Session
) -> None:
    assert request(client, rental_setup).status_code == 201
    assert request(client, rental_setup).status_code == 409
    rental_setup["item"].availability = False
    db_session.commit()
    assert request(client, rental_setup, role="peer").status_code == 409


def test_participant_privacy_and_actions(
    client: TestClient, rental_setup: dict[str, Any]
) -> None:
    rental = request(client, rental_setup).json()
    for role in ("outsider", "stranger"):
        assert (
            client.get(
                f"/api/v1/rentals/{rental['id']}", headers=rental_setup["headers"][role]
            ).status_code
            == 404
        )
        assert (
            client.get("/api/v1/rentals", headers=rental_setup["headers"][role]).json()[
                "total"
            ]
            == 0
        )
        for verb in ("accept", "reject", "start", "return", "cancel"):
            assert (
                action(client, rental_setup, rental["id"], verb, role).status_code
                == 404
            )
    for verb in ("accept", "reject", "start", "return"):
        assert (
            action(client, rental_setup, rental["id"], verb, "borrower").status_code
            == 403
        )
    assert (
        action(client, rental_setup, rental["id"], "cancel", "borrower").json()[
            "status"
        ]
        == "CANCELLED"
    )
    assert client.get("/api/v1/rentals").status_code == 401


@pytest.mark.parametrize(("start", "end"), [(1, 3), (2, 4), (0, 2), (0, 4)])
def test_overlaps_block_acceptance(
    client: TestClient, rental_setup: dict[str, Any], start: int, end: int
) -> None:
    first = request(client, rental_setup).json()
    second = request(client, rental_setup, "peer", start, end).json()
    assert action(client, rental_setup, first["id"], "accept").status_code == 200
    assert action(client, rental_setup, second["id"], "accept").status_code == 409
    assert request(client, rental_setup, "stranger", start, end).status_code == 409
    assert action(client, rental_setup, first["id"], "cancel").status_code == 200
    assert action(client, rental_setup, second["id"], "accept").status_code == 200


def test_adjacent_bookings_and_rejection(
    client: TestClient, rental_setup: dict[str, Any]
) -> None:
    first = request(client, rental_setup).json()
    adjacent = request(client, rental_setup, "peer", 3, 5).json()
    assert action(client, rental_setup, first["id"], "accept").status_code == 200
    assert action(client, rental_setup, adjacent["id"], "accept").status_code == 200
    rejected = request(client, rental_setup, "peer", 5, 7).json()
    assert (
        action(client, rental_setup, rejected["id"], "reject").json()["status"]
        == "REJECTED"
    )
    assert action(client, rental_setup, rejected["id"], "accept").status_code == 409
    page = client.get(
        "/api/v1/rentals",
        headers=rental_setup["headers"]["owner"],
        params={"role": "owner", "status": "ACCEPTED", "limit": 1},
    ).json()
    assert page["total"] == 2 and len(page["rentals"]) == 1


def test_accept_rechecks_availability_and_community(
    client: TestClient, rental_setup: dict[str, Any], db_session: Session
) -> None:
    rental = request(client, rental_setup).json()
    rental_setup["item"].availability = False
    db_session.commit()
    assert action(client, rental_setup, rental["id"], "accept").status_code == 409
    rental_setup["item"].availability = True
    rental_setup["users"]["borrower"].community_id = rental_setup["users"][
        "outsider"
    ].community_id
    db_session.commit()
    assert action(client, rental_setup, rental["id"], "accept").status_code == 403


def test_past_acceptance_and_cancellation_deadline(
    client: TestClient, rental_setup: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    pending = request(client, rental_setup).json()
    accepted = request(client, rental_setup, "peer", 3, 5).json()
    assert action(client, rental_setup, accepted["id"], "accept").status_code == 200
    monkeypatch.setattr(service, "today_utc", lambda: TODAY + timedelta(days=3))
    assert action(client, rental_setup, pending["id"], "accept").status_code == 409
    assert (
        action(client, rental_setup, accepted["id"], "cancel", "borrower").status_code
        == 404
    )
    assert (
        action(client, rental_setup, accepted["id"], "cancel", "peer").status_code
        == 409
    )


def test_clients_cannot_supply_financials_or_status(
    client: TestClient, rental_setup: dict[str, Any]
) -> None:
    payload = {
        "item_id": str(rental_setup["item"].id),
        "start_date": str(TODAY),
        "end_date": str(TODAY + timedelta(days=1)),
    }
    for key, value in [
        ("status", "ACCEPTED"),
        ("rental_amount", "0"),
        ("platform_fee", "0"),
        ("owner_id", str(rental_setup["users"]["borrower"].id)),
    ]:
        assert (
            client.post(
                "/api/v1/rentals",
                headers=rental_setup["headers"]["borrower"],
                json={**payload, key: value},
            ).status_code
            == 422
        )


def test_score_events_are_clamped_and_idempotent(
    client: TestClient, db_session: Session, rental_setup: dict[str, Any]
) -> None:
    rental = request(client, rental_setup).json()
    borrower = rental_setup["users"]["borrower"]
    borrower.nabo_score = 99
    db_session.commit()

    rental_id = uuid.UUID(rental["id"])
    assert apply_score_event(db_session, borrower.id, rental_id, "ON_TIME_RETURN")
    assert borrower.nabo_score == 100
    assert not apply_score_event(db_session, borrower.id, rental_id, "ON_TIME_RETURN")
    assert borrower.nabo_score == 100

    borrower.nabo_score = 3
    db_session.commit()
    assert apply_score_event(db_session, borrower.id, rental_id, "DAMAGED_ITEM_DISPUTE")
    assert borrower.nabo_score == 0


def test_on_time_and_late_returns_update_borrower_score(
    client: TestClient,
    db_session: Session,
    rental_setup: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    borrower = rental_setup["users"]["borrower"]
    borrower.nabo_score = 80
    db_session.commit()
    on_time = request(client, rental_setup, start=0, end=1).json()
    assert action(client, rental_setup, on_time["id"], "accept").status_code == 200
    assert action(client, rental_setup, on_time["id"], "start").status_code == 200
    returned = action(client, rental_setup, on_time["id"], "return").json()
    assert returned["borrower"]["nabo_score"] == 82
    assert returned["borrower"]["nabo_label"] == "Good"

    borrower.nabo_score = 80
    db_session.commit()
    late = request(client, rental_setup, start=0, end=1).json()
    assert action(client, rental_setup, late["id"], "accept").status_code == 200
    assert action(client, rental_setup, late["id"], "start").status_code == 200
    monkeypatch.setattr(service, "today_utc", lambda: TODAY + timedelta(days=2))
    returned = action(client, rental_setup, late["id"], "return").json()
    assert returned["borrower"]["nabo_score"] == 75


@pytest.mark.parametrize("role", ["borrower", "owner"])
def test_cancelled_accepted_booking_deducts_once(
    client: TestClient,
    db_session: Session,
    rental_setup: dict[str, Any],
    role: str,
) -> None:
    borrower = rental_setup["users"]["borrower"]
    owner = rental_setup["users"]["owner"]
    rental = request(client, rental_setup).json()
    assert action(client, rental_setup, rental["id"], "accept").status_code == 200
    cancelled = action(client, rental_setup, rental["id"], "cancel", role).json()
    db_session.refresh(borrower)
    db_session.refresh(owner)
    other = "owner" if role == "borrower" else "borrower"
    assert rental_setup["users"][role].nabo_score == 95
    assert rental_setup["users"][other].nabo_score == 100
    assert cancelled[role]["nabo_score"] == 95
    assert action(client, rental_setup, rental["id"], "cancel", role).status_code == 409
    db_session.refresh(borrower)
    db_session.refresh(owner)
    assert rental_setup["users"][role].nabo_score == 95


def test_ratings_and_damage_disputes_are_scoped_and_single_use(
    client: TestClient, db_session: Session, rental_setup: dict[str, Any]
) -> None:
    owner = rental_setup["users"]["owner"]
    borrower = rental_setup["users"]["borrower"]
    owner.nabo_score = 80
    borrower.nabo_score = 80
    db_session.commit()
    rental = request(client, rental_setup, start=0, end=1).json()
    for verb in ("accept", "start", "return"):
        assert action(client, rental_setup, rental["id"], verb).status_code == 200

    rating_url = f"/api/v1/rentals/{rental['id']}/rating"
    result = client.post(
        rating_url, headers=rental_setup["headers"]["borrower"], json={"rating": 4}
    )
    assert result.status_code == 201
    db_session.refresh(owner)
    assert owner.nabo_score == 81
    assert (
        client.post(
            rating_url, headers=rental_setup["headers"]["borrower"], json={"rating": 5}
        ).status_code
        == 409
    )
    assert (
        client.post(
            rating_url, headers=rental_setup["headers"]["owner"], json={"rating": 3}
        ).status_code
        == 201
    )
    assert (
        client.post(
            rating_url, headers=rental_setup["headers"]["stranger"], json={"rating": 5}
        ).status_code
        == 404
    )
    assert (
        client.post(
            rating_url, headers=rental_setup["headers"]["owner"], json={"rating": 6}
        ).status_code
        == 422
    )

    dispute_url = f"/api/v1/rentals/{rental['id']}/damage-dispute"
    assert (
        client.post(
            dispute_url, headers=rental_setup["headers"]["borrower"]
        ).status_code
        == 403
    )
    assert (
        client.post(dispute_url, headers=rental_setup["headers"]["owner"]).status_code
        == 201
    )
    db_session.refresh(borrower)
    assert borrower.nabo_score == 72
    assert (
        client.post(dispute_url, headers=rental_setup["headers"]["owner"]).status_code
        == 409
    )


def test_profiles_and_rental_requests_show_score_labels(
    client: TestClient, db_session: Session, rental_setup: dict[str, Any]
) -> None:
    borrower = rental_setup["users"]["borrower"]
    borrower.nabo_score = 59
    rental_setup["item"].availability = True
    db_session.commit()
    rental = request(client, rental_setup).json()
    assert rental["borrower"] == {
        "id": str(borrower.id),
        "full_name": "borrower",
        "nabo_score": 59,
        "nabo_label": "Risky",
    }
    response = client.get(
        f"/api/v1/users/{borrower.id}",
        headers=rental_setup["headers"]["owner"],
    )
    assert response.status_code == 200
    assert response.json()["nabo_label"] == "Risky"
    outsider = rental_setup["users"]["outsider"]
    assert (
        client.get(
            f"/api/v1/users/{outsider.id}",
            headers=rental_setup["headers"]["owner"],
        ).status_code
        == 404
    )
