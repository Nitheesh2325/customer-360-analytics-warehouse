"""Database configuration for Customer360."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import URL


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def get_database_url() -> URL | str:
    """Build the database URL from an explicit URL or component settings."""
    explicit_url = os.getenv("CUSTOMER360_DATABASE_URL")
    if explicit_url:
        return explicit_url

    required_settings = {
        "CUSTOMER360_DB_NAME": os.getenv("CUSTOMER360_DB_NAME"),
        "CUSTOMER360_DB_USER": os.getenv("CUSTOMER360_DB_USER"),
        "CUSTOMER360_DB_PASSWORD": os.getenv("CUSTOMER360_DB_PASSWORD"),
    }
    missing = [name for name, value in required_settings.items() if not value]
    if missing:
        raise RuntimeError(
            "Missing Customer360 database settings: " + ", ".join(missing)
        )

    return URL.create(
        drivername="postgresql+psycopg2",
        username=required_settings["CUSTOMER360_DB_USER"],
        password=required_settings["CUSTOMER360_DB_PASSWORD"],
        host=os.getenv("CUSTOMER360_DB_HOST", "localhost"),
        port=int(os.getenv("CUSTOMER360_DB_PORT", "5432")),
        database=required_settings["CUSTOMER360_DB_NAME"],
    )
