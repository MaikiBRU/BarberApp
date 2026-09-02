"""Appointment visibility, ownership and status transitions."""

from tests.factories import SEED, ApiHelper, next_business_day


def make_booking(api: ApiHelper, email: str = SEED.customer_email) -> dict:
    """Create one appointment and return the response body."""
    service_id = api.service_id()
    barber = api.barber()
    day = next_business_day()
    slot = api.first_slot(
        service_id=service_id,
        day=day,
        barber_id=barber["id"],
    )
    response = api.client.post(
        "/api/v1/appointments",
        headers=api.auth(email),
        json={
            "barber_id": barber["user_id"],
            "service_id": service_id,
            "starts_at": slot,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_owner_body_is_never_trusted_for_ownership(api: ApiHelper) -> None:
    """A customer_id in the payload is ignored, not honoured."""
    service_id = api.service_id()
    barber = api.barber()
    day = next_business_day()
    slot = api.first_slot(
        service_id=service_id,
        day=day,
        barber_id=barber["id"],
    )
    victim = api.register("victima@example.com")

    response = api.client.post(
        "/api/v1/appointments",
        headers=api.auth(SEED.customer_email),
        json={
            "barber_id": barber["user_id"],
            "service_id": service_id,
            "starts_at": slot,
            "customer_id": victim["user"]["id"],
        },
    )

    assert response.status_code == 201
    assert response.json()["customer"]["id"] != victim["user"]["id"]


def test_duration_from_the_body_is_ignored(api: ApiHelper) -> None:
    """The stored duration comes from the service, not the client."""
    service_id = api.service_id()
    barber = api.barber()
    day = next_business_day()
    slot = api.first_slot(
        service_id=service_id,
        day=day,
        barber_id=barber["id"],
    )

    response = api.client.post(
        "/api/v1/appointments",
        headers=api.auth(SEED.customer_email),
        json={
            "barber_id": barber["user_id"],
            "service_id": service_id,
            "starts_at": slot,
            "duration_minutes": 5,
        },
    )

    assert response.status_code == 201
    assert response.json()["duration_minutes"] == 45


def test_customer_cannot_read_another_customer_booking(
    api: ApiHelper,
) -> None:
    """An appointment id belonging to someone else reads as missing."""
    booking = make_booking(api)
    api.register("intruso@example.com")

    response = api.client.get(
        f"/api/v1/appointments/{booking['id']}",
        headers=api.auth("intruso@example.com"),
    )

    assert response.status_code == 404


def test_listing_is_scoped_to_the_caller(api: ApiHelper) -> None:
    """A customer only ever sees their own rows, count included."""
    make_booking(api)
    api.register("otro@example.com")

    listing = api.client.get(
        "/api/v1/appointments",
        headers=api.auth("otro@example.com"),
    ).json()

    assert listing["total"] == 0
    assert listing["items"] == []


def test_admin_sees_every_appointment(api: ApiHelper) -> None:
    """Administrators are not scoped to their own rows."""
    make_booking(api)

    listing = api.client.get(
        "/api/v1/appointments",
        headers=api.auth(SEED.admin_email),
    ).json()

    assert listing["total"] == 1
    assert listing["items"][0]["customer"]["email"] is not None


def test_customer_does_not_see_the_barber_contact_details(
    api: ApiHelper,
) -> None:
    """Staff contact data stays out of customer-facing payloads."""
    booking = make_booking(api)

    assert booking["barber"]["name"] == "Tomas"
    assert booking["barber"]["email"] is None
    assert booking["barber"]["phone"] is None


def test_assigned_barber_sees_the_customer_contact_details(
    api: ApiHelper,
) -> None:
    """A barber needs to reach the customer of their own booking."""
    booking = make_booking(api)

    detail = api.client.get(
        f"/api/v1/appointments/{booking['id']}",
        headers=api.auth(SEED.barber_email),
    ).json()

    assert detail["customer"]["name"] == "Cliente Demo"
    assert detail["customer"]["phone"] == "+54 11 5555 5555"
