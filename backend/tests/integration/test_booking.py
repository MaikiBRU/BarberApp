"""End-to-end behaviour of the booking engine."""

from datetime import UTC, datetime, timedelta

from tests.factories import SEED, ApiHelper, next_business_day


def book(
    api: ApiHelper,
    *,
    email: str,
    barber_user_id: str,
    service_id: str,
    starts_at: str,
    extra_ids: list[str] | None = None,
):
    """Post a booking request and return the raw response."""
    return api.client.post(
        "/api/v1/appointments",
        headers=api.auth(email),
        json={
            "barber_id": barber_user_id,
            "service_id": service_id,
            "starts_at": starts_at,
            "extra_ids": extra_ids or [],
            "payment_method": "cash",
        },
    )


def test_customer_books_a_slot_returned_by_availability(
    api: ApiHelper,
) -> None:
    """The happy path: pick an offered slot and get a pending booking."""
    service_id = api.service_id()
    barber = api.barber()
    day = next_business_day()
    slot = api.first_slot(
        service_id=service_id,
        day=day,
        barber_id=barber["id"],
    )

    response = book(
        api,
        email=SEED.customer_email,
        barber_user_id=barber["user_id"],
        service_id=service_id,
        starts_at=slot,
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "pending"
    assert body["duration_minutes"] == 45
    assert body["service"]["name"] == "Corte clasico"
    assert body["total_price_cents"] == 1300000
    assert body["can_cancel"] is True


def test_booked_slot_disappears_from_availability(api: ApiHelper) -> None:
    """A booked slot stops being offered to the next customer."""
    service_id = api.service_id()
    barber = api.barber()
    day = next_business_day()
    slot = api.first_slot(
        service_id=service_id,
        day=day,
        barber_id=barber["id"],
    )

    book(
        api,
        email=SEED.customer_email,
        barber_user_id=barber["user_id"],
        service_id=service_id,
        starts_at=slot,
    )

    after = api.availability(
        service_id=service_id,
        day=day,
        barber_id=barber["id"],
    )
    offered = [item["starts_at"] for item in after["barbers"][0]["slots"]]
    assert slot not in offered


def test_two_customers_cannot_take_the_same_slot(api: ApiHelper) -> None:
    """The second booking for the same barber and time is rejected."""
    service_id = api.service_id()
    barber = api.barber()
    day = next_business_day()
    slot = api.first_slot(
        service_id=service_id,
        day=day,
        barber_id=barber["id"],
    )

    first = book(
        api,
        email=SEED.customer_email,
        barber_user_id=barber["user_id"],
        service_id=service_id,
        starts_at=slot,
    )
    api.register("segundo@example.com")
    second = book(
        api,
        email="segundo@example.com",
        barber_user_id=barber["user_id"],
        service_id=service_id,
        starts_at=slot,
    )

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["error"]["type"] == "slot_unavailable"


def test_overlapping_slot_is_rejected_when_start_differs(
    api: ApiHelper,
) -> None:
    """A 45-minute service blocks the 15 minutes that follow it."""
    service_id = api.service_id()
    barber = api.barber()
    day = next_business_day()
    slot = api.first_slot(
        service_id=service_id,
        day=day,
        barber_id=barber["id"],
    )
    book(
        api,
        email=SEED.customer_email,
        barber_user_id=barber["user_id"],
        service_id=service_id,
        starts_at=slot,
    )

    overlapping = datetime.fromisoformat(slot) + timedelta(minutes=15)
    api.register("tercero@example.com")
    response = book(
        api,
        email="tercero@example.com",
        barber_user_id=barber["user_id"],
        service_id=service_id,
        starts_at=overlapping.isoformat(),
    )

    assert response.status_code == 409


def test_a_second_barber_keeps_the_same_time_available(
    api: ApiHelper,
) -> None:
    """Booking one barber does not block their colleague."""
    service_id = api.service_id()
    first_barber = api.barber("Tomas")
    second_barber = api.barber("Lucia")
    day = next_business_day()
    slot = api.first_slot(
        service_id=service_id,
        day=day,
        barber_id=first_barber["id"],
    )
    book(
        api,
        email=SEED.customer_email,
        barber_user_id=first_barber["user_id"],
        service_id=service_id,
        starts_at=slot,
    )

    api.register("cuarto@example.com")
    response = book(
        api,
        email="cuarto@example.com",
        barber_user_id=second_barber["user_id"],
        service_id=service_id,
        starts_at=slot,
    )

    assert response.status_code == 201


def test_booking_in_the_past_is_rejected(api: ApiHelper) -> None:
    """A start time behind the lead window never reaches the database."""
    past = datetime.now(UTC) - timedelta(days=1)

    response = book(
        api,
        email=SEED.customer_email,
        barber_user_id=api.barber()["user_id"],
        service_id=api.service_id(),
        starts_at=past.replace(microsecond=0).isoformat(),
    )

    assert response.status_code == 422
    assert response.json()["error"]["type"] == "business_rule_error"


def test_slot_off_the_grid_is_rejected(api: ApiHelper) -> None:
    """A time the availability endpoint never offered is refused."""
    service_id = api.service_id()
    barber = api.barber()
    day = next_business_day()
    slot = api.first_slot(
        service_id=service_id,
        day=day,
        barber_id=barber["id"],
    )
    off_grid = datetime.fromisoformat(slot) + timedelta(minutes=7)

    response = book(
        api,
        email=SEED.customer_email,
        barber_user_id=barber["user_id"],
        service_id=service_id,
        starts_at=off_grid.isoformat(),
    )

    assert response.status_code == 409


def test_extras_extend_the_duration_and_the_price(api: ApiHelper) -> None:
    """Adding a 15-minute extra grows the booked window and total."""
    service_id = api.service_id()
    extra_id = api.extra_id()
    barber = api.barber()
    day = next_business_day()
    slot = api.first_slot(
        service_id=service_id,
        day=day,
        barber_id=barber["id"],
        extra_ids=[extra_id],
    )

    response = book(
        api,
        email=SEED.customer_email,
        barber_user_id=barber["user_id"],
        service_id=service_id,
        starts_at=slot,
        extra_ids=[extra_id],
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["duration_minutes"] == 60
    assert body["extras_price_cents"] == 300000
    assert body["total_price_cents"] == 1600000
