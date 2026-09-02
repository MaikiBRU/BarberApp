"""Appointment status transitions and the cancellation policy."""

from tests.factories import SEED, ApiHelper, next_business_day
from tests.integration.test_appointments import make_booking


def test_barber_confirms_and_completes_their_booking(
    api: ApiHelper,
) -> None:
    """The assigned barber walks the appointment through its states."""
    booking = make_booking(api)
    headers = api.auth(SEED.barber_email)

    confirmed = api.client.patch(
        f"/api/v1/appointments/{booking['id']}/status",
        headers=headers,
        json={"status": "confirmed"},
    )
    completed = api.client.patch(
        f"/api/v1/appointments/{booking['id']}/status",
        headers=headers,
        json={"status": "completed"},
    )

    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "confirmed"
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"


def test_completed_appointment_is_final(api: ApiHelper) -> None:
    """No transition leaves a terminal state."""
    booking = make_booking(api)
    headers = api.auth(SEED.admin_email)
    api.client.patch(
        f"/api/v1/appointments/{booking['id']}/status",
        headers=headers,
        json={"status": "completed"},
    )

    response = api.client.patch(
        f"/api/v1/appointments/{booking['id']}/status",
        headers=headers,
        json={"status": "confirmed"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["type"] == "business_rule_error"


def test_customer_may_only_cancel(api: ApiHelper) -> None:
    """A customer cannot confirm or complete their own booking."""
    booking = make_booking(api)
    headers = api.auth(SEED.customer_email)

    confirm = api.client.patch(
        f"/api/v1/appointments/{booking['id']}/status",
        headers=headers,
        json={"status": "confirmed"},
    )
    cancel = api.client.patch(
        f"/api/v1/appointments/{booking['id']}/status",
        headers=headers,
        json={"status": "cancelled", "cancellation_reason": "Imprevisto"},
    )

    assert confirm.status_code == 403
    assert cancel.status_code == 200
    assert cancel.json()["status"] == "cancelled"
    assert cancel.json()["cancellation_reason"] == "Imprevisto"


def test_customer_cannot_touch_another_persons_booking(
    api: ApiHelper,
) -> None:
    """Transitions are refused on rows the caller cannot even read."""
    booking = make_booking(api)
    api.register("ajeno@example.com")

    response = api.client.patch(
        f"/api/v1/appointments/{booking['id']}/status",
        headers=api.auth("ajeno@example.com"),
        json={"status": "cancelled"},
    )

    assert response.status_code == 404


def test_unassigned_barber_cannot_change_the_status(
    api: ApiHelper,
) -> None:
    """A barber has no authority over a colleague's appointment."""
    booking = make_booking(api)

    response = api.client.patch(
        f"/api/v1/appointments/{booking['id']}/status",
        headers=api.auth(SEED.second_barber_email),
        json={"status": "confirmed"},
    )

    assert response.status_code == 404


def test_cancelling_frees_the_slot_again(api: ApiHelper) -> None:
    """A cancelled appointment stops blocking the barber agenda."""
    service_id = api.service_id()
    barber = api.barber()
    day = next_business_day()
    slot = api.first_slot(
        service_id=service_id,
        day=day,
        barber_id=barber["id"],
    )
    booking = make_booking(api)

    api.client.patch(
        f"/api/v1/appointments/{booking['id']}/status",
        headers=api.auth(SEED.admin_email),
        json={"status": "cancelled"},
    )

    after = api.availability(
        service_id=service_id,
        day=day,
        barber_id=barber["id"],
    )
    offered = [item["starts_at"] for item in after["barbers"][0]["slots"]]
    assert slot in offered


def test_cancellation_reason_requires_a_cancellation(
    api: ApiHelper,
) -> None:
    """Sending a reason with another transition is a validation error."""
    booking = make_booking(api)

    response = api.client.patch(
        f"/api/v1/appointments/{booking['id']}/status",
        headers=api.auth(SEED.admin_email),
        json={"status": "confirmed", "cancellation_reason": "n/a"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["type"] == "validation_error"


def test_listing_pages_and_reports_the_total(api: ApiHelper) -> None:
    """Pagination metadata reflects the full result set."""
    make_booking(api)

    listing = api.client.get(
        "/api/v1/appointments",
        headers=api.auth(SEED.admin_email),
        params={"limit": 1, "offset": 0},
    ).json()

    assert listing["limit"] == 1
    assert listing["offset"] == 0
    assert listing["total"] == 1
    assert len(listing["items"]) == 1


def test_allowed_transitions_are_reported_per_viewer(
    api: ApiHelper,
) -> None:
    """The API tells each client exactly which actions it may take."""
    booking = make_booking(api)

    customer_view = api.client.get(
        f"/api/v1/appointments/{booking['id']}",
        headers=api.auth(SEED.customer_email),
    ).json()
    barber_view = api.client.get(
        f"/api/v1/appointments/{booking['id']}",
        headers=api.auth(SEED.barber_email),
    ).json()

    assert customer_view["allowed_transitions"] == ["cancelled"]
    assert "confirmed" in barber_view["allowed_transitions"]
    assert "completed" in barber_view["allowed_transitions"]
