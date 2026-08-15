"""Focused behavior tests for Customer360 SCD and fact loading."""

from __future__ import annotations

import datetime
import sys
import unittest
from pathlib import Path

import pandas as pd
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    Text,
    create_engine,
    func,
    select,
)
from sqlalchemy.pool import StaticPool


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from etl.load import load_incremental_table, prepare_fact_sales  # noqa: E402
from etl.scd2 import build_row_hash, load_scd2_dimension  # noqa: E402
from etl.validation import validate_fact_records  # noqa: E402


def build_engine():
    engine = create_engine(
        "sqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    with engine.begin() as connection:
        connection.exec_driver_sql("ATTACH DATABASE ':memory:' AS warehouse")
    return engine


def create_scd_tables(engine) -> tuple[Table, Table]:
    metadata = MetaData()
    customer = Table(
        "dim_customer",
        metadata,
        Column("customer_key", Integer, primary_key=True, autoincrement=True),
        Column("customer_id", String(50), nullable=False),
        Column("customer_name", String(150)),
        Column("row_hash", String(64), nullable=False),
        Column("effective_from", DateTime, nullable=False),
        Column("effective_to", DateTime),
        Column("is_current", Boolean, nullable=False),
        Column("is_deleted", Boolean, nullable=False, default=False),
        Column("created_at", DateTime),
        Column("updated_at", DateTime),
        schema="warehouse",
    )
    rejected = Table(
        "rejected_records",
        metadata,
        Column("rejection_id", Integer, primary_key=True, autoincrement=True),
        Column("source_name", String(150)),
        Column("table_name", String(100)),
        Column("business_key", String(255)),
        Column("raw_record", JSON),
        Column("rejection_reason", Text),
        Column("rejected_at", DateTime),
        Column("resolved", Boolean),
        schema="warehouse",
    )
    metadata.create_all(engine)
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE UNIQUE INDEX warehouse.ux_test_customer_current "
            "ON dim_customer(customer_id) WHERE is_current = 1"
        )
    return customer, rejected


def create_fact_tables(engine) -> dict[str, Table]:
    metadata = MetaData()
    tables = {
        "customer": Table(
            "dim_customer", metadata,
            Column("customer_key", Integer, primary_key=True),
            Column("customer_id", String(50), nullable=False),
            Column("is_current", Boolean, nullable=False),
            Column("is_deleted", Boolean, nullable=False),
            schema="warehouse",
        ),
        "product": Table(
            "dim_product", metadata,
            Column("product_key", Integer, primary_key=True),
            Column("product_id", Integer, nullable=False),
            Column("is_current", Boolean, nullable=False),
            Column("is_deleted", Boolean, nullable=False),
            schema="warehouse",
        ),
        "location": Table(
            "dim_location", metadata,
            Column("location_key", Integer, primary_key=True),
            Column("location_id", Integer, nullable=False, unique=True),
            schema="warehouse",
        ),
        "channel": Table(
            "dim_channel", metadata,
            Column("channel_key", Integer, primary_key=True),
            Column("channel_id", Integer, nullable=False, unique=True),
            schema="warehouse",
        ),
        "date": Table(
            "dim_date", metadata,
            Column("date_key", Integer, primary_key=True),
            Column("full_date", Date, nullable=False, unique=True),
            schema="warehouse",
        ),
        "fact": Table(
            "fact_sales", metadata,
            Column("sales_key", Integer, primary_key=True, autoincrement=True),
            Column("order_id", Integer, nullable=False, unique=True),
            Column("customer_key", Integer, nullable=False),
            Column("product_key", Integer, nullable=False),
            Column("location_key", Integer, nullable=False),
            Column("channel_key", Integer, nullable=False),
            Column("date_key", Integer, nullable=False),
            Column("quantity", Integer, nullable=False),
            Column("unit_price", Numeric(12, 2), nullable=False),
            Column("discount", Numeric(5, 2), nullable=False),
            Column("total_amount", Numeric(14, 2), nullable=False),
            schema="warehouse",
        ),
        "rejected": Table(
            "rejected_records", metadata,
            Column("rejection_id", Integer, primary_key=True, autoincrement=True),
            Column("source_name", String(150)),
            Column("table_name", String(100)),
            Column("business_key", String(255)),
            Column("raw_record", JSON),
            Column("rejection_reason", Text),
            Column("rejected_at", DateTime),
            Column("resolved", Boolean),
            schema="warehouse",
        ),
    }
    metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(
            tables["customer"].insert(),
            [
                {"customer_key": 10, "customer_id": "C1", "is_current": False, "is_deleted": False},
                {"customer_key": 11, "customer_id": "C1", "is_current": True, "is_deleted": False},
            ],
        )
        connection.execute(
            tables["product"].insert(),
            {"product_key": 21, "product_id": 1, "is_current": True, "is_deleted": False},
        )
        connection.execute(
            tables["location"].insert(), {"location_key": 31, "location_id": 1}
        )
        connection.execute(
            tables["channel"].insert(), {"channel_key": 41, "channel_id": 1}
        )
        connection.execute(
            tables["date"].insert(), {"date_key": 20240101, "full_date": datetime.date(2024, 1, 1)}
        )
    return tables


class SCD2BehaviorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = build_engine()
        self.customer, self.rejected = create_scd_tables(self.engine)

    def tearDown(self) -> None:
        self.engine.dispose()

    def test_new_unchanged_changed_and_single_current_version(self) -> None:
        first = pd.DataFrame([{"customer_id": "C1", "customer_name": "Alpha"}])
        self.assertEqual(
            load_scd2_dimension(first, "dim_customer", "customer_id", self.engine)[
                "inserted"
            ],
            1,
        )
        self.assertEqual(
            load_scd2_dimension(first, "dim_customer", "customer_id", self.engine)[
                "unchanged"
            ],
            1,
        )
        changed = pd.DataFrame([{"customer_id": "C1", "customer_name": "Beta"}])
        self.assertEqual(
            load_scd2_dimension(changed, "dim_customer", "customer_id", self.engine)[
                "updated"
            ],
            1,
        )
        with self.engine.connect() as connection:
            rows = connection.execute(select(self.customer)).mappings().all()
        self.assertEqual(len(rows), 2)
        self.assertEqual(sum(bool(row["is_current"]) for row in rows), 1)
        self.assertEqual(next(row for row in rows if row["is_current"])["customer_name"], "Beta")

    def test_stale_supplied_hash_cannot_hide_change(self) -> None:
        first = pd.DataFrame(
            [{"customer_id": "C1", "customer_name": "Alpha", "row_hash": "stale"}]
        )
        second = pd.DataFrame(
            [{"customer_id": "C1", "customer_name": "Beta", "row_hash": "stale"}]
        )
        load_scd2_dimension(first, "dim_customer", "customer_id", self.engine)
        result = load_scd2_dimension(second, "dim_customer", "customer_id", self.engine)
        self.assertEqual(result["updated"], 1)

    def test_delete_expires_current_version(self) -> None:
        load_scd2_dimension(
            pd.DataFrame([{"customer_id": "C1", "customer_name": "Alpha"}]),
            "dim_customer",
            "customer_id",
            self.engine,
        )
        result = load_scd2_dimension(
            pd.DataFrame([{"customer_id": "C1", "operation": "DELETE"}]),
            "dim_customer",
            "customer_id",
            self.engine,
        )
        self.assertEqual(result["deleted"], 1)
        with self.engine.connect() as connection:
            row = connection.execute(select(self.customer)).mappings().one()
        self.assertFalse(row["is_current"])
        self.assertTrue(row["is_deleted"])
        self.assertIsNotNone(row["effective_to"])

    def test_missing_key_is_persisted_as_rejected(self) -> None:
        result = load_scd2_dimension(
            pd.DataFrame([{"customer_id": None, "customer_name": "Invalid"}]),
            "dim_customer",
            "customer_id",
            self.engine,
        )
        self.assertEqual(result["quarantined"], 1)
        with self.engine.connect() as connection:
            count = connection.execute(
                select(func.count()).select_from(self.rejected)
            ).scalar_one()
        self.assertEqual(count, 1)

    def test_hash_is_derived_from_controlled_attributes(self) -> None:
        columns = {"customer_id", "customer_name", "row_hash"}
        first = build_row_hash(
            {"customer_id": "C1", "customer_name": "Alpha", "row_hash": "same"},
            columns,
            "customer_id",
        )
        second = build_row_hash(
            {"customer_id": "C1", "customer_name": "Beta", "row_hash": "same"},
            columns,
            "customer_id",
        )
        self.assertNotEqual(first, second)


class FactValidationTests(unittest.TestCase):
    def valid_fact(self) -> dict[str, object]:
        return {
            "order_id": 1,
            "customer_id": "C1",
            "product_id": 1,
            "location_id": 1,
            "channel_id": 1,
            "order_date": "2024-01-01",
            "quantity": 2,
            "unit_price": 10.0,
            "discount": 0.1,
            "total_amount": 18.0,
        }

    def test_amount_and_measure_validation(self) -> None:
        invalid = self.valid_fact()
        invalid.update({"quantity": 0, "unit_price": -1, "discount": 2, "total_amount": 99})
        valid, rejected = validate_fact_records(pd.DataFrame([invalid]))
        self.assertTrue(valid.empty)
        self.assertEqual(len(rejected), 1)
        self.assertIn("quantity", rejected[0].reason)
        self.assertIn("unit_price", rejected[0].reason)
        self.assertIn("discount", rejected[0].reason)

    def test_total_amount_must_reconcile(self) -> None:
        invalid = self.valid_fact()
        invalid["total_amount"] = 19.0
        valid, rejected = validate_fact_records(pd.DataFrame([invalid]))
        self.assertTrue(valid.empty)
        self.assertIn("does not reconcile", rejected[0].reason)

    def test_currency_rounding_accepts_source_amount_at_exact_cent(self) -> None:
        valid_fact = self.valid_fact()
        valid_fact.update(
            {
                "quantity": 3,
                "unit_price": 86.85,
                "discount": 0.1,
                "total_amount": 234.50,
            }
        )
        valid, rejected = validate_fact_records(pd.DataFrame([valid_fact]))
        self.assertEqual(len(valid), 1)
        self.assertEqual(rejected, [])

    def test_reconciliation_accepts_one_cent_source_rounding_difference(self) -> None:
        valid_fact = self.valid_fact()
        valid_fact.update(
            {
                "quantity": 5,
                "unit_price": 2103.73,
                "discount": 0.1,
                "total_amount": 9466.78,
            }
        )
        valid, rejected = validate_fact_records(pd.DataFrame([valid_fact]))
        self.assertEqual(len(valid), 1)
        self.assertEqual(rejected, [])


class FactLoadBehaviorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = build_engine()
        self.tables = create_fact_tables(self.engine)

    def tearDown(self) -> None:
        self.engine.dispose()

    @staticmethod
    def source_fact(product_id: int = 1) -> pd.DataFrame:
        return pd.DataFrame(
            [{
                "order_id": 1,
                "customer_id": "C1",
                "product_id": product_id,
                "location_id": 1,
                "channel_id": 1,
                "order_date": "2024-01-01",
                "quantity": 2,
                "unit_price": 10.0,
                "discount": 0.1,
                "total_amount": 18.0,
            }]
        )

    def test_fact_uses_current_active_dimension_versions(self) -> None:
        prepared = prepare_fact_sales(self.source_fact(), self.engine)
        self.assertEqual(prepared.loc[0, "customer_key"], 11)
        self.assertEqual(prepared.loc[0, "product_key"], 21)
        self.assertEqual(prepared.loc[0, "date_key"], 20240101)

    def test_invalid_source_reference_is_persisted(self) -> None:
        prepared = prepare_fact_sales(self.source_fact(product_id=999), self.engine)
        self.assertTrue(prepared.empty)
        with self.engine.connect() as connection:
            row = connection.execute(select(self.tables["rejected"])).mappings().one()
        self.assertEqual(row["business_key"], "1")
        self.assertIn("source reference", row["rejection_reason"])

    def test_repeat_fact_load_skips_existing_order_id(self) -> None:
        prepared = prepare_fact_sales(self.source_fact(), self.engine)
        first = load_incremental_table(
            prepared, "fact_sales", "order_id", self.engine
        )
        second = load_incremental_table(
            prepared, "fact_sales", "order_id", self.engine
        )
        self.assertEqual(first, {"inserted": 1, "skipped": 0})
        self.assertEqual(second, {"inserted": 0, "skipped": 1})
        with self.engine.connect() as connection:
            count = connection.execute(
                select(func.count()).select_from(self.tables["fact"])
            ).scalar_one()
        self.assertEqual(count, 1)


if __name__ == "__main__":
    unittest.main()
