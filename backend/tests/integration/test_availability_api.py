"""Availability responses driven by schedule and catalog changes."""

from tests.factories import SEED, ApiHelper, next_business_day


def book(
    api: ApiHelper,
    *,
    email: str,
    barber_user_id: str,
    service_id: str,
    starts_at: str,
):
    """Post a booking request and return the raw response."""
    return api.client.post(
        "/api/v1/appointments",
        headers=api.auth(email),
        json={
            "barber_id": barber_user_id,
            "service_id": service_id,
            "starts_at": starts_at,
        },
    )


def test_longer_service_offers_fewer_slots(api: ApiHelper) -> None:
    """Availability reflects the duration of the chosen service."""
    day = next_business_day()
    barber_id = api.barber()["id"]

    short = api.availability(
        service_id=api.service_id("Corte clasico"),
        day=day,
        barber_id=barber_id,
    )
    long = api.availability(
        service_id=api.service_id("Corte largo"),
        day=day,
        barber_id=barber_id,
    )

    assert short["duration_minutes"] == 45
    assert long["duration_minutes"] == 90
    assert len(short["barbers"][0]["slots"]) > len(
        long["barbers"][0]["slots"]
    )


def test_time_off_removes_slots_from_availability(api: ApiHelper) -> None:
    """An absence blocks the barber for the whole window."""
    service_id = api.service_id()
    barber = api.barber()
    day = next_business_day()
    before = api.availability(
        service_id=service_id,
        day=day,
        barber_id=barber["id"],
    )
    first_slot = before["barbers"][0]["slots"][0]

    blocked = api.client.post(
        f"/api/v1/schedule/barbers/{barber['id']}/time-off",
        headers=api.auth(SEED.admin_email),
        json={
            "starts_at": first_slot["starts_at"],
            "ends_at": first_slot["ends_at"],
            "reason": "Turno medico",
        },
    )
    assert blocked.status_code == 201, blocked.text

    after = api.availability(
        service_id=service_id,
        day=day,
        barber_id=barber["id"],
    )
    offered = [item["starts_at"] for item in after["barbers"][0]["slots"]]
    assert first_slot["starts_at"] not in offered


def test_closed_day_offers_no_slots(api: ApiHelper) -> None:
    """Marking a weekday closed empties its availability."""
    day = next_business_day()
    api.client.put(
        "/api/v1/schedule/business-hours",
        headers=api.auth(SEED.admin_email),
        json={
            "days": [
                {
                    "weekday": day.weekday(),
                    "opens_at": "09:00:00",
                    "closes_at": "19:00:00",
                    "is_closed": True,
                }
            ]
        },
    )

    payload = api.availability(
        service_id=api.service_id(),
        day=day,
        barber_id=api.barber()["id"],
    )

    assert payload["is_open"] is False
    assert payload["barbers"] == []


def test_inactive_service_cannot_be_booked(api: ApiHelper) -> None:
    """Deactivating a service removes it from the booking flow."""
    service_id = api.service_id()
    barber = api.barber()
    day = next_business_day()
    slot = api.first_slot(
        service_id=service_id,
        day=day,
        barber_id=barber["id"],
    )
    api.client.patch(
        f"/api/v1/catalog/services/{service_id}",
        headers=api.auth(SEED.admin_email),
        json={"is_active": False},
    )

    response = book(
        api,
        email=SEED.customer_email,
        barber_user_id=barber["user_id"],
        service_id=service_id,
        starts_at=slot,
    )

    assert response.status_code == 404


def test_inactive_barber_cannot_be_booked(api: ApiHelper) -> None:
    """Deactivating a barber removes them from the booking flow."""
    service_id = api.service_id()
    barber = api.barber()
    day = next_business_day()
    slot = api.first_slot(
        service_id=service_id,
        day=day,
        barber_id=barber["id"],
    )
    api.client.patch(
        f"/api/v1/users/barbers/{barber['id']}",
        headers=api.auth(SEED.admin_email),
        json={"is_active": False},
    )

    response = book(
        api,
        email=SEED.customer_email,
        barber_user_id=barber["user_id"],
        service_id=service_id,
        starts_at=slot,
    )

    assert response.status_code == 404
