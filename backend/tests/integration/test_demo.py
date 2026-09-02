"""The portfolio demo sandbox: isolation, personas and quotas."""

from fastapi.testclient import TestClient

from tests.factories import ApiHelper


def start(client: TestClient) -> dict:
    """Create a sandbox and return the start payload."""
    response = client.post("/api/v1/demo/session")
    assert response.status_code == 201, response.text
    return response.json()


def auth(payload: dict) -> dict[str, str]:
    """Return the Authorization header for a sandbox token."""
    return {"Authorization": f"Bearer {payload['access_token']}"}


def test_config_is_public(client: TestClient) -> None:
    """The landing page reads the limits without a sandbox."""
    response = client.get("/api/v1/demo/config")

    assert response.status_code == 200
    body = response.json()
    assert body["enabled"] is True
    assert body["limits"]["max_appointments"] > 0
    assert {persona["role"] for persona in body["personas"]} == {
        "customer",
        "barber",
        "admin",
    }


def test_session_starts_as_a_customer_with_a_seeded_shop(
    client: TestClient,
) -> None:
    """A visitor lands on a populated product, not an empty form."""
    payload = start(client)
    headers = auth(payload)

    assert payload["session"]["state"]["active_role"] == "customer"

    services = client.get("/api/v1/catalog/services", headers=headers)
    barbers = client.get("/api/v1/users/barbers", headers=headers)
    hours = client.get("/api/v1/schedule/business-hours", headers=headers)

    assert len(services.json()) == 4
    assert len(barbers.json()) == 2
    assert len(hours.json()) == 7


def test_sandbox_cannot_see_the_real_shop(api: ApiHelper) -> None:
    """The seeded real shop is invisible from inside a sandbox."""
    real_services = {item["name"] for item in api.client.get(
        "/api/v1/catalog/services"
    ).json()}
    payload = start(api.client)

    demo_services = {
        item["name"]
        for item in api.client.get(
            "/api/v1/catalog/services", headers=auth(payload)
        ).json()
    }

    assert "Corte largo" in real_services
    assert "Corte largo" not in demo_services


def test_the_real_shop_cannot_see_a_sandbox(api: ApiHelper) -> None:
    """Rows created in a sandbox never leak into the real catalog."""
    start(api.client)

    public = {
        item["name"]
        for item in api.client.get("/api/v1/catalog/services").json()
    }

    assert public == {"Corte clásico", "Corte largo"}


def test_two_sandboxes_are_isolated(client: TestClient) -> None:
    """One visitor's changes never reach another's sandbox."""
    first = start(client)
    second = start(client)

    admin = client.post(
        "/api/v1/demo/session/role",
        headers=auth(first),
        json={"role": "admin"},
    ).json()
    created = client.post(
        "/api/v1/catalog/services",
        headers=auth(admin),
        json={
            "name": "Servicio solo del primero",
            "duration_minutes": 30,
            "price_cents": 100,
        },
    )
    assert created.status_code == 201

    names = {
        item["name"]
        for item in client.get(
            "/api/v1/catalog/services", headers=auth(second)
        ).json()
    }
    assert "Servicio solo del primero" not in names


def test_visitor_switches_between_the_three_roles(
    client: TestClient,
) -> None:
    """The same sandbox is reachable as customer, barber and admin."""
    payload = start(client)

    for role in ("barber", "admin", "customer"):
        switched = client.post(
            "/api/v1/demo/session/role",
            headers=auth(payload),
            json={"role": role},
        )
        assert switched.status_code == 200, switched.text
        assert switched.json()["session"]["state"]["active_role"] == role

        me = client.get("/api/v1/auth/me", headers=auth(switched.json()))
        assert me.json()["role"] == role


def test_demo_dashboard_reports_seeded_activity(client: TestClient) -> None:
    """The seed leaves enough history for the figures to be real."""
    payload = start(client)
    admin = client.post(
        "/api/v1/demo/session/role",
        headers=auth(payload),
        json={"role": "admin"},
    ).json()

    summary = client.get(
        "/api/v1/dashboard/summary", headers=auth(admin)
    ).json()

    assert summary["active_barbers"] == 2
    assert summary["active_services"] == 4
    assert summary["upcoming_count"] >= 1
    assert summary["today_revenue_cents"] > 0
