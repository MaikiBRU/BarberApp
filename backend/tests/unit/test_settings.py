"""Configuration parsing and production safety checks."""

import pytest

from core.config import Settings


def build(**overrides) -> Settings:
    """Build settings from explicit values, ignoring the ambient env."""
    defaults = {
        "APP_ENV": "development",
        "DEBUG": True,
        "JWT_SECRET_KEY": "a" * 40,
        "CORS_ORIGINS": "http://localhost:3000",
        "SHOP_TIMEZONE": "America/Argentina/Buenos_Aires",
    }
    return Settings(**{**defaults, **overrides})


def test_comma_separated_cors_origins_are_parsed() -> None:
    """A comma-separated allowlist loads without a JSON decode error."""
    settings = build(
        CORS_ORIGINS="http://localhost:3000, http://127.0.0.1:3000",
    )

    assert settings.get_cors_origins() == [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


def test_blank_cors_entries_are_dropped() -> None:
    """Trailing separators do not produce empty origins."""
    settings = build(CORS_ORIGINS="http://localhost:3000,, ")

    assert settings.get_cors_origins() == ["http://localhost:3000"]


def test_unknown_timezone_is_rejected() -> None:
    """A typo in the shop timezone fails at startup, not at runtime."""
    with pytest.raises(ValueError):
        build(SHOP_TIMEZONE="Mars/Olympus_Mons")


def test_development_defaults_are_not_flagged() -> None:
    """Local development never trips the production guard."""
    assert build().production_config_errors() == []


def test_production_rejects_the_development_secret() -> None:
    """Booting production with the shipped secret is refused."""
    errors = build(
        APP_ENV="production",
        DEBUG=False,
        JWT_SECRET_KEY="dev-secret-key-change-me-min-32-chars",
    ).production_config_errors()

    assert any("JWT_SECRET_KEY" in error for error in errors)


def test_production_rejects_debug_mode() -> None:
    """Debug mode leaks internals, so production refuses to start."""
    errors = build(
        APP_ENV="production",
        DEBUG=True,
    ).production_config_errors()

    assert any("DEBUG" in error for error in errors)


def test_production_rejects_a_wildcard_cors_allowlist() -> None:
    """A wildcard origin is not an allowlist."""
    errors = build(
        APP_ENV="production",
        DEBUG=False,
        CORS_ORIGINS="*",
    ).production_config_errors()

    assert any("CORS_ORIGINS" in error for error in errors)


def test_valid_production_config_passes() -> None:
    """A correctly configured production process starts."""
    assert (
        build(
            APP_ENV="production",
            DEBUG=False,
            JWT_SECRET_KEY="x" * 48,
            CORS_ORIGINS="https://barberapp.example",
        ).production_config_errors()
        == []
    )


def test_database_url_is_upgraded_to_the_async_driver() -> None:
    """A plain PostgreSQL URL is rewritten for asyncpg."""
    settings = build(
        DATABASE_URL="postgresql://user:pass@localhost:5432/barberapp",
    )

    assert settings.async_database_url.startswith("postgresql+asyncpg://")
