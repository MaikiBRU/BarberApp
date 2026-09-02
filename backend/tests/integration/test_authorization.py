"""Role enforcement across the protected surface."""

from tests.factories import SEED, ApiHelper


def test_customer_cannot_reach_admin_catalog_endpoints(
    api: ApiHelper,
) -> None:
    """Creating a service requires the admin role."""
    headers = api.auth(SEED.customer_email)

    response = api.client.post(
        "/api/v1/catalog/services",
        headers=headers,
        json={
            "name": "Servicio pirata",
            "duration_minutes": 30,
            "price_cents": 1000,
        },
    )

    assert response.status_code == 403
    assert response.json()["error"]["type"] == "authorization_error"


def test_barber_cannot_create_services(api: ApiHelper) -> None:
    """Barbers manage their agenda, not the catalog."""
    response = api.client.post(
        "/api/v1/catalog/services",
        headers=api.auth(SEED.barber_email),
        json={
            "name": "Otro servicio",
            "duration_minutes": 30,
            "price_cents": 1000,
        },
    )

    assert response.status_code == 403


def test_customer_cannot_create_barber_accounts(api: ApiHelper) -> None:
    """Staff creation is admin-only."""
    response = api.client.post(
        "/api/v1/users/barbers",
        headers=api.auth(SEED.customer_email),
        json={
            "email": "fake@example.com",
            "password": "Password123!",
            "display_name": "Impostor",
        },
    )

    assert response.status_code == 403


def test_customer_cannot_open_the_staff_dashboard(api: ApiHelper) -> None:
    """The dashboard is limited to admins and barbers."""
    response = api.client.get(
        "/api/v1/dashboard/summary",
        headers=api.auth(SEED.customer_email),
    )

    assert response.status_code == 403


def test_barber_can_open_the_staff_dashboard(api: ApiHelper) -> None:
    """A barber sees their own operational figures."""
    response = api.client.get(
        "/api/v1/dashboard/summary",
        headers=api.auth(SEED.barber_email),
    )

    assert response.status_code == 200
    assert response.json()["active_barbers"] == 2


def test_public_barber_list_hides_contact_details(api: ApiHelper) -> None:
    """Anonymous callers never receive staff emails or phones."""
    barbers = api.client.get("/api/v1/users/barbers").json()

    assert barbers
    for barber in barbers:
        assert barber["email"] is None
        assert barber["phone"] is None


def test_admin_barber_list_includes_contact_details(
    api: ApiHelper,
) -> None:
    """Administrators need the contact data to run the shop."""
    barbers = api.client.get(
        "/api/v1/users/admin/barbers",
        headers=api.auth(SEED.admin_email),
    ).json()

    assert any(barber["email"] for barber in barbers)


def test_customer_cannot_manage_another_barber_time_off(
    api: ApiHelper,
) -> None:
    """Only admins or the barber themselves may block agenda time."""
    barber_profile_id = api.barber()["id"]

    response = api.client.post(
        f"/api/v1/schedule/barbers/{barber_profile_id}/time-off",
        headers=api.auth(SEED.customer_email),
        json={
            "starts_at": "2099-01-01T10:00:00+00:00",
            "ends_at": "2099-01-01T12:00:00+00:00",
        },
    )

    assert response.status_code == 403


def test_barber_cannot_block_a_colleague_agenda(api: ApiHelper) -> None:
    """A barber may only manage their own time off."""
    colleague_profile_id = api.barber("Lucia")["id"]

    response = api.client.post(
        f"/api/v1/schedule/barbers/{colleague_profile_id}/time-off",
        headers=api.auth(SEED.barber_email),
        json={
            "starts_at": "2099-01-01T10:00:00+00:00",
            "ends_at": "2099-01-01T12:00:00+00:00",
        },
    )

    assert response.status_code == 403


def test_inactive_account_cannot_log_in(api: ApiHelper) -> None:
    """Deactivating a barber blocks their access immediately."""
    barber_profile_id = api.barber()["id"]
    api.client.patch(
        f"/api/v1/users/barbers/{barber_profile_id}",
        headers=api.auth(SEED.admin_email),
        json={"is_active": False},
    )

    listed = api.client.get("/api/v1/users/barbers").json()
    assert all(item["display_name"] != "Tomas" for item in listed)
