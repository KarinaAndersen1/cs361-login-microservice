import os
from functools import lru_cache
from typing import Dict

from pydantic import BaseModel, Field


class Settings(BaseModel):
    # Core service
    service_name: str = Field(default="login-service")
    issuer_url: str = Field(default="http://localhost:8000")

    # JWT / OIDC
    jwt_secret: str = Field(
        default="CHANGE_ME_TO_A_LONG_RANDOM_SECRET_FOR_REAL_USE"
    )
    jwt_algorithm: str = Field(default="HS256")
    jwt_key_id: str = Field(default="demo-symmetric-key")
    access_token_minutes: int = Field(default=30)
    refresh_token_days: int = Field(default=7)

    # Clients (very simple OIDC-style validation)
    # key: client_id, value: human-readable name
    clients: Dict[str, str] = Field(
        default_factory=lambda: {"demo-client": "Demo Public Client"}
    )

    # Demo user store: username -> password (plaintext for demo)
    demo_users: Dict[str, str] = Field(
        default_factory=lambda: {
            "alice": "password123",
            "bob": "password123",
        }
    )

    log_level: str = Field(default="INFO")


@lru_cache
def get_settings() -> Settings:
    return Settings(
        issuer_url=os.getenv("ISSUER_URL", "http://localhost:8000"),
        jwt_secret=os.getenv(
            "JWT_SECRET",
            "CHANGE_ME_TO_A_LONG_RANDOM_SECRET_FOR_REAL_USE",
        ),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        jwt_key_id=os.getenv("JWT_KEY_ID", "demo-symmetric-key"),
        access_token_minutes=int(os.getenv("ACCESS_TOKEN_MINUTES", "30")),
        refresh_token_days=int(os.getenv("REFRESH_TOKEN_DAYS", "7")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )


settings = get_settings()
