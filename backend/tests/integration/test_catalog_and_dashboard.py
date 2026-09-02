"""Catalog management and dashboard figures."""

from tests.factories import SEED, ApiHelper, next_business_day


def test_admin_creates_updates_and_deactivates_a_service(
    api: ApiHelper,
) -> None:
    """The full admin catalog lifecycle works end to end."""
    headers = api.auth(SEED.admin_email)

    created = api.client.post(
        "/api/v1/catalog/services",
        headers=headers,
        json={
            "name": "Coloracion",
            "description": "Coloracion completa",
            "duration_minutes": 120,
            "price_cents": 4500000,
        },
    )
    assert created.status_code == 201
    service_id = created.json()["id"]

    updated = api.client.patch(
        f"/api/v1/catalog/services/{service_id}",
        headers=headers,
        json={"price_cents": 5000000},
    )
    assert updated.status_code == 200
    assert updated.json()["price_cents"] == 5000000

    api.client.patch(
        f"/api/v1/catalog/services/{service_id}",
        headers=headers,
        json={"is_active": False},
    )

    public = api.client.get("/api/v1/catalog/services").json()
    admin = api.client.get(
        "/api/v1/catalog/admin/services",
        headers=headers,
    ).json()

    assert all(item["id"] != service_id for item in public)
    assert any(item["id"] == service_id for item in admin)


def test_duplicate_service_names_are_rejected(api: ApiHelper) -> None:
    """The catalog refuses two services with the same name."""
    response = api.client.post(
        "/api/v1/catalog/services",
        headers=api.auth(SEED.admin_email),
        json={
            "name": "Corte clasico",
            "duration_minutes": 30,
            "price_cents": 100,
        },
    )

    assert response.status_code == 409


def test_service_validation_rejects_impossible_values(
    api: ApiHelper,
) -> None:
    """Zero-length services and negative prices are refused."""
    headers = api.auth(SEED.admin_email)

    zero_duration = api.client.post(
        "/api/v1/catalog/services",
        headers=headers,
        json={
            "name": "Servicio invalido",
            "duration_minutes": 0,
            "price_cents": 1000,
        },
    )
    negative_price = api.client.post(
        "/api/v1/catalog/services",
        headers=headers,
        json={
            "name": "Servicio gratis",
            "duration_minutes": 30,
            "price_cents": -1,
        },
    )

    assert zero_duration.status_code == 422
    assert negative_price.status_code == 422


def test_shop_id_cannot_be_injected_by_the_client(api: ApiHelper) -> None:
    """A shop_id in the payload is ignored by the create schema."""
    response = api.client.post(
        "/api/v1/catalog/services",
        headers=api.auth(SEED.admin_email),
        json={
            "name": "Servicio ajeno",
            "duration_minutes": 30,
            "price_cents": 1000,
            "shop_id": "otra-barberia",
        },
    )

    assert response.status_code == 201
    assert response.json()["shop_id"] is None


def test_admin_creates_a_barber_that_can_log_in(api: ApiHelper) -> None:
    """A created barber account is immediately usable."""
    created = api.client.post(
        "/api/v1/users/barbers",
        headers=api.auth(SEED.admin_email),
        json={
            "email": "nuevo.barbero@example.com",
            "password": "Password123!",
            "display_name": "Nico",
            "bio": "Especialista en fades",
        },
    )

    assert created.status_code == 201
    assert created.json()["display_name"] == "Nico"

    token = api.login("nuevo.barbero@example.com")
    me = api.client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me.json()["role"] == "barber"


def test_dashboard_reports_real_counts(api: ApiHelper) -> None:
    """Figures come from stored rows, not from placeholders."""
    summary = api.client.get(
        "/api/v1/dashboard/summary",
        headers=api.auth(SEED.admin_email),
    ).json()

    assert summary["active_barbers"] == 2
    assert summary["active_services"] == 2
    assert summary["today"]["pending"] == 0
    assert summary["today_revenue_cents"] == 0
    assert summary["currency"] == "ARS"


def test_dashboard_counts_a_new_booking_as_upcoming(
    api: ApiHelper,
) -> None:
    """A future booking lands in the upcoming bucket, not in today."""
    service_id = api.service_id()
    barber = api.barber()
    day = next_business_day()
    slot = api.first_slot(
        service_id=service_id,
        day=day,
        barber_id=barber["id"],
    )
    api.client.post(
        "/api/v1/appointments",
        headers=api.auth(SEED.customer_email),
        json={
            "barber_id": barber["user_id"],
            "service_id": service_id,
            "starts_at": slot,
        },
    )

    summary = api.client.get(
        "/api/v1/dashboard/summary",
        headers=api.auth(SEED.admin_email),
    ).json()

    assert summary["upcoming_count"] == 1
    assert len(summary["next_appointments"]) == 1


def test_barber_dashboard_only_counts_their_own_agenda(
    api: ApiHelper,
) -> None:
    """A barber's figures exclude a colleague's appointments."""
    service_id = api.service_id()
    colleague = api.barber("Lucia")
    day = next_business_day()
    slot = api.first_slot(
        service_id=service_id,
        day=day,
        barber_id=colleague["id"],
    )
    api.client.post(
        "/api/v1/appointments",
        headers=api.auth(SEED.customer_email),
        json={
            "barber_id": colleague["user_id"],
            "service_id": service_id,
            "starts_at": slot,
        },
    )

    own = api.client.get(
        "/api/v1/dashboard/summary",
        headers=api.auth(SEED.barber_email),
    ).json()
    colleague_view = api.client.get(
        "/api/v1/dashboard/summary",
        headers=api.auth(SEED.second_barber_email),
    ).json()

    assert own["upcoming_count"] == 0
    assert colleague_view["upcoming_count"] == 1


def test_customer_updates_their_own_profile(api: ApiHelper) -> None:
    """Profile edits are scoped to the authenticated account."""
    headers = api.auth(SEED.customer_email)

    updated = api.client.patch(
        "/api/v1/users/me/profile",
        headers=headers,
        json={"full_name": "Cliente Actualizado", "phone": "+54 11 4444"},
    )

    assert updated.status_code == 200
    assert updated.json()["full_name"] == "Cliente Actualizado"

    fetched = api.client.get("/api/v1/users/me/profile", headers=headers)
    assert fetched.json()["phone"] == "+54 11 4444"


def test_business_hours_are_readable_and_editable(api: ApiHelper) -> None:
    """Opening hours come from the database and admins can change them."""
    hours = api.client.get("/api/v1/schedule/business-hours").json()
    assert len(hours) == 7

    updated = api.client.put(
        "/api/v1/schedule/business-hours",
        headers=api.auth(SEED.admin_email),
        json={
            "days": [
                {
                    "weekday": 0,
                    "opens_at": "10:00:00",
                    "closes_at": "18:00:00",
                    "is_closed": False,
                }
            ]
        },
    )

    assert updated.status_code == 200
    monday = next(day for day in updated.json() if day["weekday"] == 0)
    assert monday["opens_at"] == "10:00:00"


def test_inverted_business_hours_are_rejected(api: ApiHelper) -> None:
    """A closing time before the opening time is a validation error."""
    response = api.client.put(
        "/api/v1/schedule/business-hours",
        headers=api.auth(SEED.admin_email),
        json={
            "days": [
                {
                    "weekday": 1,
                    "opens_at": "19:00:00",
                    "closes_at": "09:00:00",
                    "is_closed": False,
                }
            ]
        },
    )

    assert response.status_code == 422
