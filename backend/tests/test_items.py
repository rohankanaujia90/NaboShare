import pytest
from fastapi.testclient import TestClient

from tests.test_communities import auth_headers

PAYLOAD = {
    "title": "Weekend projector",
    "description": "Portable projector with HDMI cable.",
    "category": "Electronics",
    "rental_price_per_day": "150.50",
    "security_deposit": "1000.00",
    "replacement_value": "12000.00",
}


@pytest.fixture
def members(
    client: TestClient,
) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    owner = auth_headers(client, "owner@example.com")
    community = client.post(
        "/api/v1/communities",
        headers=owner,
        json={"name": "First Campus", "type": "college", "city": "Delhi"},
    ).json()
    peer = auth_headers(client, "peer@example.com")
    assert (
        client.post(
            "/api/v1/communities/join",
            headers=peer,
            json={"invite_code": community["invite_code"]},
        ).status_code
        == 200
    )
    outsider = auth_headers(client, "outsider@example.com")
    assert (
        client.post(
            "/api/v1/communities",
            headers=outsider,
            json={"name": "Other Campus", "type": "hostel", "city": "Delhi"},
        ).status_code
        == 201
    )
    return owner, peer, outsider


def test_crud_and_isolation(
    client: TestClient, members: tuple[dict[str, str], dict[str, str], dict[str, str]]
) -> None:
    owner, peer, outsider = members
    response = client.post("/api/v1/items", headers=owner, json=PAYLOAD)
    assert response.status_code == 201
    item = response.json()
    assert item["rental_price_per_day"] == "150.50"
    url = f"/api/v1/items/{item['id']}"
    assert client.get(url, headers=peer).status_code == 200
    assert client.patch(url, headers=peer, json={"title": "Changed"}).status_code == 403
    assert client.delete(url, headers=peer).status_code == 403
    assert client.get("/api/v1/items", headers=outsider).json()["total"] == 0
    assert client.get(url, headers=outsider).status_code == 404
    assert (
        client.patch(url, headers=outsider, json={"availability": False}).status_code
        == 404
    )
    assert client.delete(url, headers=outsider).status_code == 404
    changed = client.patch(
        url, headers=owner, json={"availability": False, "image_url": None}
    )
    assert changed.status_code == 200
    assert changed.json()["availability"] is False
    assert changed.json()["title"] == PAYLOAD["title"]
    assert client.delete(url, headers=owner).status_code == 204
    assert client.get(url, headers=owner).status_code == 404


def test_filters(
    client: TestClient, members: tuple[dict[str, str], dict[str, str], dict[str, str]]
) -> None:
    owner, _, outsider = members
    for headers, data in [
        (owner, PAYLOAD),
        (outsider, PAYLOAD),
        (
            owner,
            {
                **PAYLOAD,
                "title": "Camping tent",
                "description": "Two-person tent with a waterproof flysheet.",
                "category": "Camping",
                "rental_price_per_day": "300",
                "availability": False,
            },
        ),
    ]:
        assert (
            client.post("/api/v1/items", headers=headers, json=data).status_code == 201
        )
    for params in [
        {"category": "Electronics"},
        {"min_price": "100", "max_price": "200"},
        {"search": "PROJECTOR"},
        {"availability": "true"},
    ]:
        result = client.get("/api/v1/items", headers=owner, params=params)
        assert result.status_code == 200
        assert result.json()["total"] == 1
    assert (
        client.get("/api/v1/items", headers=owner, params={"search": "%"}).json()[
            "total"
        ]
        == 0
    )
    page = client.get("/api/v1/items", headers=owner, params={"limit": 1}).json()
    assert page["total"] == 2 and len(page["items"]) == 1
    assert (
        client.get(
            "/api/v1/items", headers=owner, params={"min_price": 500, "max_price": 100}
        ).status_code
        == 422
    )


def test_validation_and_membership(
    client: TestClient, members: tuple[dict[str, str], dict[str, str], dict[str, str]]
) -> None:
    owner, _, _ = members
    for change in [
        {"owner_id": "spoofed"},
        {"community_id": "spoofed"},
        {"category": "Invalid"},
        {"rental_price_per_day": "-1"},
        {"security_deposit": "1.234"},
        {"title": " "},
        {"image_url": "javascript:alert(1)"},
    ]:
        assert (
            client.post(
                "/api/v1/items", headers=owner, json={**PAYLOAD, **change}
            ).status_code
            == 422
        )
    item = client.post("/api/v1/items", headers=owner, json=PAYLOAD).json()
    for change in [{}, {"title": None}, {"owner_id": item["owner_id"]}]:
        assert (
            client.patch(
                f"/api/v1/items/{item['id']}", headers=owner, json=change
            ).status_code
            == 422
        )
    assert client.get("/api/v1/items").status_code == 401
    unassigned = auth_headers(client, "unassigned-items@example.com")
    assert client.get("/api/v1/items", headers=unassigned).status_code == 403
    assert (
        client.post("/api/v1/items", headers=unassigned, json=PAYLOAD).status_code
        == 403
    )
