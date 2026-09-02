"""Demo sandbox quotas, reset and teardown."""

from fastapi.testclient import TestClient

from tests.factories import SEED, ApiHelper, next_business_day
from tests.integration.test_demo import auth, start


def test_booking_quota_is_enforced(client: TestClient) -> None:
    """Once the sandbox allowance is used, booking is refused."""
    payload = start(client)
    headers = auth(payload)

    services = client.get(
        "/api/v1/catalog/services", headers=headers
    ).json()
    barbers = client.get("/api/v1/users/barbers", headers=headers).json()
    service = next(
        item for item in services if item["name"] == "Corte infantil"
    )

    limit = payload["session"]["limits"]["max_appointments"]
    statuses = []
    for _ in range(limit + 1):
        availability = client.get(
            "/api/v1/appointments/availability",
            headers=headers,
            params={
                "service_id": service["id"],
                "date": payload["session"]["state"]["expires_at"][:10],
                "barber_id": barbers[0]["id"],
            },
        ).json()
        slots = availability["barbers"][0]["slots"] if availability[
            "barbers"
        ] else []
        if not slots:
            break
        statuses.append(
            client.post(
                "/api/v1/appointments",
                headers=headers,
                json={
                    "barber_id": barbers[0]["user_id"],
                    "service_id": service["id"],
                    "starts_at": slots[0]["starts_at"],
                },
            ).status_code
        )

    assert 429 in statuses or len(statuses) <= limit


def test_write_quota_is_enforced(client: TestClient) -> None:
    """Catalog edits are capped so a sandbox cannot be hammered."""
    payload = start(client)
    admin = client.post(
        "/api/v1/demo/session/role",
        headers=auth(payload),
        json={"role": "admin"},
    ).json()
    headers = auth(admin)
    limit = payload["session"]["limits"]["max_writes"]

    last = 201
    for index in range(limit + 2):
        last = client.post(
            "/api/v1/catalog/services",
            headers=headers,
            json={
                "name": f"Servicio {index}",
                "duration_minutes": 30,
                "price_cents": 1000,
            },
        ).status_code
        if last == 429:
            break

    assert last == 429


def test_reset_wipes_the_sandbox_and_restores_the_quota(
    client: TestClient,
) -> None:
    """Reset gives the visitor a clean shop without a new session."""
    payload = start(client)
    admin = client.post(
        "/api/v1/demo/session/role",
        headers=auth(payload),
        json={"role": "admin"},
    ).json()
    client.post(
        "/api/v1/catalog/services",
        headers=auth(admin),
        json={
            "name": "Servicio temporal",
            "duration_minutes": 30,
            "price_cents": 1000,
        },
    )

    reset = client.post("/api/v1/demo/session/reset", headers=auth(admin))

    assert reset.status_code == 200, reset.text
    assert reset.json()["session"]["state"]["writes_used"] == 0
    names = {
        item["name"]
        for item in client.get(
            "/api/v1/catalog/services", headers=auth(reset.json())
        ).json()
    }
    assert "Servicio temporal" not in names
    assert len(names) == 4


def test_ending_a_session_revokes_its_token(client: TestClient) -> None:
    """After ending the demo, the token stops working."""
    payload = start(client)
    headers = auth(payload)

    ended = client.post("/api/v1/demo/session/end", headers=headers)
    after = client.get("/api/v1/demo/session", headers=headers)

    assert ended.status_code == 200
    assert ended.json()["status"] == "ended"
    assert after.status_code == 401


def test_registering_inside_a_sandbox_stays_in_the_sandbox(
    api: ApiHelper,
) -> None:
    """A signup made with a demo token never creates a real account."""
    payload = start(api.client)

    created = api.client.post(
        "/api/v1/auth/register",
        headers=auth(payload),
        json={
            "email": "visitante@example.com",
            "password": "Password123!",
            "full_name": "Visitante",
        },
    )
    assert created.status_code == 201

    real_login = api.client.post(
        "/api/v1/auth/login",
        json={"email": "visitante@example.com", "password": "Password123!"},
    )
    assert real_login.status_code == 401


def test_demo_token_cannot_reach_a_real_appointment(
    api: ApiHelper,
) -> None:
    """An id from the real shop is invisible to a sandbox token."""
    booking = api.client.post(
        "/api/v1/appointments",
        headers=api.auth(SEED.customer_email),
        json={
            "barber_id": api.barber()["user_id"],
            "service_id": api.service_id(),
            "starts_at": api.first_slot(
                service_id=api.service_id(),
                day=next_business_day(),
                barber_id=api.barber()["id"],
            ),
        },
    )
    assert booking.status_code == 201
    payload = start(api.client)

    response = api.client.get(
        f"/api/v1/appointments/{booking.json()['id']}",
        headers=auth(payload),
    )

    assert response.status_code == 404
