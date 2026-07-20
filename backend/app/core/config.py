from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    app_name: str = "HealthGuard AI API"
    app_version: str = "0.1.0"
    environment: Literal["development", "test", "staging", "production"] = "development"
    api_prefix: str = "/api/v1"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    docs_enabled: bool = True
    database_url: SecretStr
    redis_url: SecretStr
    token_secret: SecretStr
    access_token_minutes: int = Field(default=15, ge=5, le=60)
    refresh_token_days: int = Field(default=30, ge=1, le=90)
    cookie_secure: bool = True
    cookie_domain: str | None = None
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    google_client_id: SecretStr | None = None
    google_client_secret: SecretStr | None = None
    web_app_url: str = "http://localhost:3000"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: SecretStr | None = None
    smtp_from_email: str = "no-reply@healthguard.ai"
    record_storage_root: str = ".local/records"
    storage_backend: str = "local-private"
    record_max_upload_bytes: int = Field(default=10 * 1024 * 1024, ge=1024, le=25 * 1024 * 1024)
    record_allowed_extensions: list[str] = Field(
        default_factory=lambda: [".pdf", ".png", ".jpg", ".jpeg", ".txt"]
    )
    emergency_number: str = "112"
    emergency_country_hint: str = "India national emergency number: 112"
    account_deletion_grace_days: int = Field(default=7, ge=0, le=30)
    export_download_minutes: int = Field(default=10, ge=1, le=60)
    medical_disclaimer: str = (
        "HealthGuard AI provides educational information only and does not replace "
        "professional medical advice, diagnosis, or treatment. In an emergency, "
        "contact local emergency services immediately."
    )

    @field_validator("api_prefix")
    @classmethod
    def validate_prefix(cls, value: str) -> str:
        if not value.startswith("/") or value.endswith("/"):
            raise ValueError("API_PREFIX must start with '/' and must not end with '/'")
        return value

    @model_validator(mode="after")
    def validate_security(self) -> "Settings":
        if len(self.token_secret.get_secret_value()) < 32:
            raise ValueError("TOKEN_SECRET must contain at least 32 characters")
        if self.environment in {"staging", "production"} and not self.cookie_secure:
            raise ValueError("COOKIE_SECURE must be true outside development and test")
        if self.environment == "production":
            origins = [str(origin).rstrip("/") for origin in self.cors_origins]
            if any("localhost" in origin or "127.0.0.1" in origin for origin in origins):
                raise ValueError("Production CORS origins must not include localhost")
            if self.web_app_url.startswith("http://"):
                raise ValueError("WEB_APP_URL must use HTTPS in production")
            if self.docs_enabled:
                raise ValueError("DOCS_ENABLED must be false in production")
        if self.smtp_password and not self.smtp_username:
            raise ValueError("SMTP_USERNAME is required when SMTP_PASSWORD is set")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
