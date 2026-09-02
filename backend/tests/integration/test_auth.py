"""Registration, login and protected-endpoint behaviour."""

from fastapi.testclient import TestClient

from tests.factories import SEED, TEST_PASSWORD, ApiHelper


def test_register_returns_token_and_customer_role(api: ApiHelper) -> None:
    """Signup creates a customer and hands back a usable token."""
    payload = api.register("nuevo@example.com")

    assert payload["user"]["role"] == "customer"
    assert payload["token_type"] == "bearer"
    assert payload["expires_in"] > 0

    me = api.client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {payload['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["email"] == "nuevo@example.com"


def test_register_rejects_duplicate_email(api: ApiHelper) -> None:
    """A second signup with the same email conflicts."""
    api.register("dup@example.com")

    response = api.client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "password": TEST_PASSWORD},
    )

    assert response.status_code == 409
    assert response.json()["error"]["type"] == "conflict"


def test_register_cannot_self_assign_a_privileged_role(
    api: ApiHelper,
) -> None:
    """Signup refuses any role other than customer."""
    response = api.client.post(
        "/api/v1/auth/register",
        json={
            "email": "escalate@example.com",
            "password": TEST_PASSWORD,
            "role": "admin",
        },
    )

    assert response.status_code == 422


def test_register_rejects_short_passwords(api: ApiHelper) -> None:
    """The minimum password length is enforced server-side."""
    response = api.client.post(
        "/api/v1/auth/register",
        json={"email": "short@example.com", "password": "abc"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["type"] == "validation_error"


def test_login_with_wrong_password_is_rejected(api: ApiHelper) -> None:
    """Bad credentials return 401 without confirming the account."""
    response = api.client.post(
        "/api/v1/auth/login",
        json={"email": SEED.admin_email, "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert (
        response.json()["error"]["message"]
        == "Email o contraseña incorrectos."
    )


def test_login_hides_whether_an_account_exists(api: ApiHelper) -> None:
    """An unknown email produces the same error as a wrong password."""
    unknown = api.client.post(
        "/api/v1/auth/login",
        json={"email": "ghost@example.com", "password": TEST_PASSWORD},
    )
    wrong = api.client.post(
        "/api/v1/auth/login",
        json={"email": SEED.admin_email, "password": "wrong-password"},
    )

    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json() == wrong.json()


def test_protected_endpoint_requires_a_token(client: TestClient) -> None:
    """An anonymous call to a protected route is unauthorized."""
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_protected_endpoint_rejects_a_forged_token(
    client: TestClient,
) -> None:
    """A token that fails signature verification is rejected."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not-a-real-token"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["type"] == "authentication_error"


def test_error_responses_use_one_envelope(client: TestClient) -> None:
    """Framework and domain errors share the same response shape."""
    response = client.get("/api/v1/appointments/does-not-exist")

    assert response.status_code == 401
    body = response.json()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"type", "message", "details"}
