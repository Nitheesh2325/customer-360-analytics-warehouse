"""Initialize Customer360 objects in an explicitly selected local database."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.engine import Engine, URL, make_url  # noqa: E402

from etl.config import get_database_url  # noqa: E402


DATABASE_DIR = PROJECT_ROOT / "database"
DATE_START = "2023-01-01"
DATE_END = "2025-12-31"
EXPECTED_DATE_ROWS = 1096
PROTECTED_DATABASES = {"postgres", "template0", "template1"}


def validate_target(database_url: str | URL, confirmation: str) -> str:
    """Require a confirmed development or test database name."""
    url = make_url(database_url)
    database_name = url.database
    if not database_name:
        raise ValueError("The database URL must include a database name.")
    if database_name.lower() in PROTECTED_DATABASES:
        raise ValueError(f"Refusing to initialize protected database: {database_name}")
    if not database_name.lower().endswith(("_dev", "_test")):
        raise ValueError("Database name must end with _dev or _test.")
    if confirmation != database_name:
        raise ValueError("--confirm-database must exactly match the URL database name.")
    return database_name


def assert_safe_existing_state(engine: Engine) -> None:
    """Refuse to alter an unknown database that already has warehouse tables."""
    with engine.connect() as connection:
        existing_tables = set(
            connection.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'warehouse'"
                )
            ).scalars()
        )
        if existing_tables and "bootstrap_metadata" not in existing_tables:
            raise RuntimeError(
                "Refusing to modify an existing warehouse schema that was not "
                "created by the Customer360 bootstrap."
            )
        if "bootstrap_metadata" in existing_tables:
            version = connection.execute(
                text(
                    "SELECT bootstrap_version FROM warehouse.bootstrap_metadata "
                    "ORDER BY bootstrap_version DESC LIMIT 1"
                )
            ).scalar_one_or_none()
            if version != 1:
                raise RuntimeError(f"Unsupported bootstrap version: {version}")


def execute_sql_file(engine: Engine, path: Path) -> None:
    """Execute one trusted, version-controlled PostgreSQL SQL file."""
    sql = path.read_text(encoding="utf-8")
    with engine.begin() as connection:
        connection.exec_driver_sql(sql)


def validate_bootstrap(engine: Engine) -> dict[str, object]:
    """Validate required objects, constraints, indexes, and dates."""
    required_tables = {
        "bootstrap_metadata",
        "dim_customer",
        "dim_product",
        "dim_location",
        "dim_channel",
        "dim_date",
        "fact_sales",
        "etl_run_log",
        "cdc_audit_log",
        "rejected_records",
    }
    with engine.connect() as connection:
        database_name = connection.execute(text("SELECT current_database()" )).scalar_one()
        tables = set(
            connection.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'warehouse'"
                )
            ).scalars()
        )
        missing_tables = sorted(required_tables - tables)
        if missing_tables:
            raise RuntimeError(f"Missing warehouse tables: {missing_tables}")

        date_result = connection.execute(
            text(
                "SELECT COUNT(*), MIN(full_date), MAX(full_date), "
                "COUNT(DISTINCT full_date) FROM warehouse.dim_date"
            )
        ).one()
        normalized_dates = (
            date_result[0],
            str(date_result[1]),
            str(date_result[2]),
            date_result[3],
        )
        expected_dates = (EXPECTED_DATE_ROWS, DATE_START, DATE_END, EXPECTED_DATE_ROWS)
        if normalized_dates != expected_dates:
            raise RuntimeError(f"Unexpected dim_date validation result: {date_result}")

        constraint_names = set(
            connection.execute(
                text(
                    "SELECT constraint_name FROM information_schema.table_constraints "
                    "WHERE table_schema = 'warehouse'"
                )
            ).scalars()
        )
        index_names = set(
            connection.execute(
                text("SELECT indexname FROM pg_indexes WHERE schemaname = 'warehouse'")
            ).scalars()
        )

    required_constraints = {
        "dim_customer_pkey",
        "dim_product_pkey",
        "dim_location_location_id_key",
        "dim_channel_channel_id_key",
        "dim_date_full_date_key",
        "fact_sales_order_id_key",
    }
    required_indexes = {
        "ux_dim_customer_current_business_key",
        "ux_dim_product_current_business_key",
        "ix_fact_sales_customer_key",
        "ix_fact_sales_product_key",
        "ix_fact_sales_location_key",
        "ix_fact_sales_channel_key",
        "ix_fact_sales_date_key",
    }
    missing_constraints = sorted(required_constraints - constraint_names)
    missing_indexes = sorted(required_indexes - index_names)
    if missing_constraints:
        raise RuntimeError(f"Required constraints are missing: {missing_constraints}")
    if missing_indexes:
        raise RuntimeError(f"Required indexes are missing: {missing_indexes}")
    return {"database": database_name, "date_rows": date_result[0], "tables": tables}


def initialize_database(
    database_url: str | URL,
    confirmation: str,
) -> dict[str, object]:
    """Create missing objects, populate dates, and validate the result."""
    validate_target(database_url, confirmation)
    engine = create_engine(database_url, pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            actual_database = connection.execute(text("SELECT current_database()" )).scalar_one()
        if actual_database != confirmation:
            raise RuntimeError("Connected database does not match the confirmed database.")
        assert_safe_existing_state(engine)
        execute_sql_file(engine, DATABASE_DIR / "schema.sql")
        execute_sql_file(engine, DATABASE_DIR / "populate_dim_date.sql")
        execute_sql_file(engine, PROJECT_ROOT / "sql" / "views.sql")
        return validate_bootstrap(engine)
    finally:
        engine.dispose()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database-url",
        help="Explicit PostgreSQL URL. Defaults to configured Customer360 settings.",
    )
    parser.add_argument(
        "--confirm-database",
        required=True,
        help="Exact _dev or _test database name expected in the URL.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    database_url = args.database_url or get_database_url()
    result = initialize_database(database_url, args.confirm_database)
    print(
        f"Initialized {result['database']} with {len(result['tables'])} warehouse "
        f"tables and {result['date_rows']} date rows."
    )


if __name__ == "__main__":
    main()
