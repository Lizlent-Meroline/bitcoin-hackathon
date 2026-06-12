"""Environment-backed settings for the SolarSats backend."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./solarsats.db")
    satoshis_per_kwh: int = int(os.getenv("SATOSHIS_PER_KWH", "50"))
    meter_secret_key: str = os.getenv(
        "METER_HMAC_SECRET",
        os.getenv("SECRET_KEY", "change-this-secret"),
    )


settings = Settings()
