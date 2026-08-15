"""Focused validation for the Customer360 database bootstrap."""

from __future__ import annotations

import datetime
import os
import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_SQL = (PROJECT_ROOT / "database" / "schema.sql").read_text(encoding="utf-8")
DATE_SQL = (PROJECT_ROOT / "database" / "populate_dim_date.sql").read_text(
    encoding="utf-8"
)
VIEW_SQL = (PROJECT_ROOT / "sql" / "views.sql").read_text(encoding="utf-8")


class BootstrapContractTests(unittest.TestCase):
    def test_required_tables_are_declared(self) -> None:
        for table in (
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
        ):
            self.assertRegex(
                SCHEMA_SQL,
                rf"CREATE TABLE IF NOT EXISTS warehouse\.{table}\s*\(",
            )

    def test_loader_business_keys_and_scd_invariants_are_declared(self) -> None:
        for expression in (
            "location_id INTEGER NOT NULL UNIQUE",
            "channel_id INTEGER NOT NULL UNIQUE",
            "order_id BIGINT NOT NULL UNIQUE",
            "ux_dim_customer_current_business_key",
            "ux_dim_product_current_business_key",
            "WHERE is_current",
        ):
            self.assertIn(expression, SCHEMA_SQL)

    def test_fact_foreign_keys_and_join_indexes_are_declared(self) -> None:
        for dimension in ("customer", "product", "location", "channel", "date"):
            self.assertIn(f"ix_fact_sales_{dimension}_key", SCHEMA_SQL)
        self.assertEqual(SCHEMA_SQL.count("REFERENCES warehouse.dim_"), 5)

    def test_loader_columns_exist_in_schema(self) -> None:
        loader_columns = {
            "dim_customer": {
                "customer_id", "customer_name", "email", "phone", "address",
                "city", "state", "country", "customer_segment", "loyalty_tier",
                "signup_date", "source_system", "row_hash", "effective_from",
                "effective_to", "is_current", "is_deleted", "created_at", "updated_at",
            },
            "dim_product": {
                "product_id", "product_name", "category", "subcategory", "brand",
                "supplier", "unit_cost", "selling_price", "source_system", "row_hash",
                "effective_from", "effective_to", "is_current", "is_deleted",
                "created_at", "updated_at",
            },
            "fact_sales": {
                "order_id", "customer_key", "product_key", "location_key",
                "channel_key", "date_key", "quantity", "unit_price", "discount",
                "total_amount",
            },
        }
        for table, columns in loader_columns.items():
            match = re.search(
                rf"CREATE TABLE IF NOT EXISTS warehouse\.{table}\s*\((.*?)\n\);",
                SCHEMA_SQL,
                re.DOTALL,
            )
            self.assertIsNotNone(match)
            table_sql = match.group(1)
            for column in columns:
                self.assertRegex(table_sql, rf"(?m)^\s*{column}\s")

    def test_date_dimension_range_is_exact_and_repeat_safe(self) -> None:
        self.assertIn("DATE '2023-01-01'", DATE_SQL)
        self.assertIn("DATE '2025-12-31'", DATE_SQL)
        self.assertIn("ON CONFLICT (date_key) DO NOTHING", DATE_SQL)
        start = datetime.date(2023, 1, 1)
        end = datetime.date(2025, 12, 31)
        self.assertEqual((end - start).days + 1, 1096)

    def test_schema_uses_idempotent_object_creation(self) -> None:
        create_statements = re.findall(r"CREATE (?:TABLE|SCHEMA|INDEX)", SCHEMA_SQL)
        safe_statements = re.findall(
            r"CREATE (?:TABLE|SCHEMA|INDEX) IF NOT EXISTS", SCHEMA_SQL
        )
        self.assertEqual(len(create_statements), len(safe_statements))

    def test_reporting_view_exposes_retained_query_columns(self) -> None:
        for column in (
            "order_id",
            "full_date",
            "month",
            "month_name",
            "year",
            "is_weekend",
            "customer_id",
            "customer_name",
            "customer_segment",
            "loyalty_tier",
            "product_id",
            "product_name",
            "category",
            "city",
            "state",
            "country",
            "region",
            "channel_name",
            "channel_type",
            "quantity",
            "unit_price",
            "total_amount",
        ):
            self.assertRegex(VIEW_SQL, rf"(?m)^\s+[^\n]*\b{column}\b")


@unittest.skipUnless(
    os.getenv("CUSTOMER360_TEST_DATABASE_URL"),
    "Set CUSTOMER360_TEST_DATABASE_URL to an explicit isolated *_test database.",
)
class BootstrapPostgreSQLIntegrationTests(unittest.TestCase):
    def test_clean_and_repeat_initialization(self) -> None:
        from scripts.init_database import initialize_database
        from sqlalchemy.engine import make_url

        database_url = os.environ["CUSTOMER360_TEST_DATABASE_URL"]
        database_name = make_url(database_url).database
        self.assertIsNotNone(database_name)
        self.assertTrue(database_name.endswith("_test"))
        first = initialize_database(database_url, database_name)
        second = initialize_database(database_url, database_name)
        self.assertEqual(first["date_rows"], 1096)
        self.assertEqual(second["date_rows"], 1096)
        self.assertEqual(first["tables"], second["tables"])


if __name__ == "__main__":
    unittest.main()
