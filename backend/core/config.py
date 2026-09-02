"""Application settings loaded from environment variables."""

from functools import lru_cache
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import AliasChoices, Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

INSECURE_JWT_SECRETS = frozenset(
    {
        "dev-secret-key-change-me-min-32-chars",
        "change-this-secret-key-before-production",
    }
)


class Settings(BaseSettings):
    """Runtime configuration for the API."""

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Application ---------------------------------------------------
    app_name: str = Field("BarberApp", validation_alias="APP_NAME")
    app_env: str = Field("development", validation_alias="APP_ENV")
    debug: bool = Field(
        True,
        validation_alias=AliasChoices("DEBUG", "APP_DEBUG"),
    )
    sql_echo: bool = Field(False, validation_alias="SQL_ECHO")
    version: str = "1.0.0"
    log_level: str = Field("INFO", validation_alias="LOG_LEVEL")

    # Kept as a raw string: pydantic-settings JSON-decodes complex types
    # straight from the environment, before any validator runs, so a
    # comma-separated list declared as list[str] fails to load at all.
    cors_origins: str = Field(
        "http://localhost:3000,http://127.0.0.1:3000",
        validation_alias=AliasChoices("CORS_ORIGINS", "API_CORS_ORIGINS"),
    )

    # --- Database ------------------------------------------------------
    database_url: str | None = Field(None, validation_alias="DATABASE_URL")
    postgres_host: str = Field(
        "localhost",
        validation_alias=AliasChoices("POSTGRES_HOST", "DB_HOST"),
    )
    postgres_port: int = Field(
        5432,
        validation_alias=AliasChoices("POSTGRES_PORT", "DB_PORT"),
    )
    postgres_user: str = Field(
        "postgres",
        validation_alias=AliasChoices("POSTGRES_USER", "DB_USER"),
    )
    postgres_password: str = Field(
        "postgres",
        validation_alias=AliasChoices("POSTGRES_PASSWORD", "DB_PASSWORD"),
    )
    postgres_db: str = Field(
        "barberapp",
        validation_alias=AliasChoices("POSTGRES_DB", "DB_NAME"),
    )
    postgres_pool_size: int = Field(
        5,
        validation_alias=AliasChoices("POSTGRES_POOL_SIZE", "DB_POOL_SIZE"),
    )
    postgres_max_overflow: int = Field(
        10,
        validation_alias=AliasChoices("POSTGRES_MAX_OVERFLOW"),
    )
    postgres_pool_pre_ping: bool = True

    # --- Authentication ------------------------------------------------
    jwt_secret_key: str = Field(
        "dev-secret-key-change-me-min-32-chars",
        validation_alias=AliasChoices("JWT_SECRET_KEY", "SECRET_KEY"),
    )
    jwt_algorithm: str = Field("HS256", validation_alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        60,
        validation_alias=AliasChoices(
            "JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
            "ACCESS_TOKEN_EXPIRE_MINUTES",
        ),
    )

    # --- Rate limiting -------------------------------------------------
    rate_limit_enabled: bool = Field(
        True,
        validation_alias="RATE_LIMIT_ENABLED",
    )
    rate_limit_auth_max_requests: int = Field(
        10,
        validation_alias="RATE_LIMIT_AUTH_MAX_REQUESTS",
    )
    rate_limit_auth_window_seconds: int = Field(
        60,
        validation_alias="RATE_LIMIT_AUTH_WINDOW_SECONDS",
    )

    # --- Booking policy ------------------------------------------------
    shop_timezone: str = Field(
        "America/Argentina/Buenos_Aires",
        validation_alias="SHOP_TIMEZONE",
    )
    currency: str = Field("ARS", validation_alias="CURRENCY")
    booking_slot_minutes: int = Field(
        15,
        ge=5,
        le=60,
        validation_alias="BOOKING_SLOT_MINUTES",
    )
    booking_min_lead_minutes: int = Field(
        60,
        ge=0,
        validation_alias="BOOKING_MIN_LEAD_MINUTES",
    )
    booking_max_advance_days: int = Field(
        60,
        ge=1,
        le=365,
        validation_alias="BOOKING_MAX_ADVANCE_DAYS",
    )
    booking_cancellation_cutoff_minutes: int = Field(
        120,
        ge=0,
        validation_alias="BOOKING_CANCELLATION_CUTOFF_MINUTES",
    )

    @field_validator("shop_timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        """Fail fast when the configured IANA timezone is unknown."""
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError(f"Unknown IANA timezone: {value}") from exc
        return value

    @computed_field  # type: ignore[prop-decorator]
    @property
    def async_database_url(self) -> str:
        """Return a SQLAlchemy async database URL."""
        if self.database_url:
            return self.database_url.replace(
                "postgresql://",
                "postgresql+asyncpg://",
                1,
            )

        return (
            "postgresql+asyncpg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def is_production(self) -> bool:
        """Whether the app runs in a production-like environment."""
        return self.app_env.lower() in {"production", "prod"}

    @property
    def timezone(self) -> ZoneInfo:
        """Return the shop timezone used for business hours."""
        return ZoneInfo(self.shop_timezone)

    def get_cors_origins(self) -> list[str]:
        """Return the configured CORS origins as a normalized list."""
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    def production_config_errors(self) -> list[str]:
        """Return blocking misconfigurations for production startup."""
        if not self.is_production:
            return []

        errors: list[str] = []
        if self.jwt_secret_key in INSECURE_JWT_SECRETS:
            errors.append(
                "JWT_SECRET_KEY still uses a development default.",
            )
        if len(self.jwt_secret_key) < 32:
            errors.append("JWT_SECRET_KEY must be at least 32 characters.")
        if self.debug:
            errors.append("DEBUG must be disabled in production.")
        origins = self.get_cors_origins()
        if not origins or "*" in origins:
            errors.append(
                "CORS_ORIGINS must be an explicit allowlist in production.",
            )
        if self.sql_echo:
            errors.append("SQL_ECHO must be disabled in production.")
        return errors


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()


settings = get_settings()
