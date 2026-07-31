"""
Load Module
Customer 360 Analytics Warehouse

Responsibilities
----------------
- Connect to PostgreSQL securely.
- Route customer and product dimensions through SCD Type 2.
- Load location, channel, and sales tables incrementally.
- Prevent duplicate business keys.
- Record every table load in warehouse.etl_run_log.
"""

from __future__ import annotations

import os
import re
from datetime import datetime
from typing import Any

import pandas as pd
from sqlalchemy import MetaData, Table, create_engine, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Engine

from etl.scd2 import load_scd2_dimension


# ============================================================
# DATABASE CONNECTION
# ============================================================

DATABASE_PASSWORD = os.getenv("CUSTOMER360_DB_PASSWORD")

if not DATABASE_PASSWORD:
    raise RuntimeError(
        "CUSTOMER360_DB_PASSWORD is not set. "
        "Set it in PowerShell before running the pipeline."
    )


DATABASE_URL = (
    f"postgresql+psycopg2://postgres:{DATABASE_PASSWORD}"
    "@localhost:5432/customer360_dw"
)


def get_engine() -> Engine:
    """
    Create and return a PostgreSQL SQLAlchemy engine.
    """
    return create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    )


# ============================================================
# TABLE CONFIGURATION
# ============================================================

TABLE_KEYS = {
    "dim_customer": "customer_id",
    "dim_product": "product_id",
    "dim_location": "location_id",
    "dim_channel": "channel_id",
    "fact_sales": "order_id",
}


SCD2_TABLES = {
    "dim_customer",
    "dim_product",
}


# ============================================================
# IDENTIFIER VALIDATION
# ============================================================

def validate_identifier(identifier: str) -> None:
    """
    Validate dynamic SQL table and column identifiers.
    """
    pattern = r"[A-Za-z_][A-Za-z0-9_]*"

    if not re.fullmatch(pattern, identifier):
        raise ValueError(
            f"Unsafe SQL identifier: {identifier}"
        )


# ============================================================
# ETL LOGGING
# ============================================================

def write_etl_log(
    table_name: str,
    start_time: datetime,
    end_time: datetime,
    rows_loaded: int,
    rows_skipped: int,
    status: str,
    error_message: str | None = None,
) -> None:
    """
    Insert one table-load result into warehouse.etl_run_log.
    """

    query = text(
        """
        INSERT INTO warehouse.etl_run_log
        (
            pipeline_name,
            table_name,
            start_time,
            end_time,
            rows_loaded,
            rows_skipped,
            status,
            error_message
        )
        VALUES
        (
            :pipeline_name,
            :table_name,
            :start_time,
            :end_time,
            :rows_loaded,
            :rows_skipped,
            :status,
            :error_message
        )
        """
    )

    values = {
        "pipeline_name": "Customer 360 ETL Pipeline",
        "table_name": table_name,
        "start_time": start_time,
        "end_time": end_time,
        "rows_loaded": rows_loaded,
        "rows_skipped": rows_skipped,
        "status": status,
        "error_message": error_message,
    }

    engine = get_engine()

    with engine.begin() as connection:
        connection.execute(
            query,
            values,
        )


# ============================================================
# DATA CONVERSION HELPERS
# ============================================================

def make_postgres_safe(value: Any) -> Any:
    """
    Convert pandas and NumPy values into PostgreSQL-safe values.
    """

    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()

    if hasattr(value, "item"):
        try:
            return value.item()
        except (TypeError, ValueError):
            pass

    return value


def convert_business_key_to_database_type(
    value: Any,
    database_column: Any,
) -> Any:
    """
    Convert a source business key to the reflected PostgreSQL type.

    This prevents errors such as:

    character varying = integer
    """

    safe_value = make_postgres_safe(value)

    if safe_value is None:
        return None

    try:
        python_type = database_column.type.python_type
    except (AttributeError, NotImplementedError):
        return safe_value

    if python_type is str:
        return str(safe_value)

    if python_type is int:
        return int(safe_value)

    if python_type is float:
        return float(safe_value)

    if python_type is bool:
        if isinstance(safe_value, str):
            normalized = safe_value.strip().lower()

            if normalized in {"true", "1", "yes", "y"}:
                return True

            if normalized in {"false", "0", "no", "n"}:
                return False

        return bool(safe_value)

    return safe_value


def prepare_records(
    dataframe: pd.DataFrame,
) -> list[dict[str, Any]]:
    """
    Convert a DataFrame into PostgreSQL-safe dictionaries.
    """

    records: list[dict[str, Any]] = []

    raw_records = dataframe.to_dict(
        orient="records"
    )

    for raw_record in raw_records:
        clean_record = {
            column: make_postgres_safe(value)
            for column, value in raw_record.items()
        }

        records.append(clean_record)

    return records


def filter_record_for_table(
    record: dict[str, Any],
    warehouse_table: Table,
) -> dict[str, Any]:
    """
    Keep only columns that exist in the destination PostgreSQL table.

    Surrogate keys generated by PostgreSQL are excluded.
    """

    table_columns = {
        column.name
        for column in warehouse_table.columns
    }

    filtered_record: dict[str, Any] = {}

    for column_name, value in record.items():
        if column_name not in table_columns:
            continue

        column = warehouse_table.c[column_name]

        if column.primary_key and (
            column.autoincrement is True
            or column.autoincrement == "auto"
            or column.default is not None
            or column.server_default is not None
        ):
            continue

        filtered_record[column_name] = value

    return filtered_record


# ============================================================
# SCD TYPE 2 LOAD
# ============================================================

def load_historical_dimension(
    dataframe: pd.DataFrame,
    table_name: str,
    business_key: str,
    engine: Engine,
) -> dict[str, int]:
    """
    Load customer or product history using SCD Type 2.
    """

    return load_scd2_dimension(
        dataframe=dataframe,
        table_name=table_name,
        business_key=business_key,
        engine=engine,
    )


# ============================================================
# STANDARD INCREMENTAL LOAD
# ============================================================

def load_incremental_table(
    dataframe: pd.DataFrame,
    table_name: str,
    business_key: str,
    engine: Engine,
) -> dict[str, int]:
    """
    Insert new records and skip existing business keys.

    Used for:
    - dim_location
    - dim_channel
    - fact_sales
    """

    stats = {
        "inserted": 0,
        "skipped": 0,
    }

    if dataframe.empty:
        return stats

    if business_key not in dataframe.columns:
        raise ValueError(
            f"Required business-key column "
            f"'{business_key}' was not found "
            f"in DataFrame for {table_name}."
        )

    original_row_count = len(dataframe)

    clean_dataframe = (
        dataframe
        .drop_duplicates(
            subset=[business_key],
            keep="last",
        )
        .copy()
    )

    duplicate_source_rows = (
        original_row_count - len(clean_dataframe)
    )

    stats["skipped"] += duplicate_source_rows

    metadata = MetaData()

    warehouse_table = Table(
        table_name,
        metadata,
        schema="warehouse",
        autoload_with=engine,
    )

    if business_key not in warehouse_table.c:
        raise ValueError(
            f"warehouse.{table_name} does not contain "
            f"business-key column '{business_key}'."
        )

    business_key_column = warehouse_table.c[
        business_key
    ]

    records = prepare_records(
        clean_dataframe
    )

    with engine.begin() as connection:
        for record in records:
            if business_key not in record:
                stats["skipped"] += 1
                continue

            key_value = convert_business_key_to_database_type(
                value=record.get(business_key),
                database_column=business_key_column,
            )

            if (
                key_value is None
                or str(key_value).strip() == ""
            ):
                stats["skipped"] += 1
                continue

            record[business_key] = key_value

            filtered_record = filter_record_for_table(
                record=record,
                warehouse_table=warehouse_table,
            )

            statement = (
                insert(warehouse_table)
                .values(**filtered_record)
                .on_conflict_do_nothing(
                    index_elements=[business_key]
                )
            )

            result = connection.execute(
                statement
            )

            if result.rowcount == 1:
                stats["inserted"] += 1
            else:
                stats["skipped"] += 1

    return stats

# ============================================================
# FACT SALES SURROGATE-KEY LOOKUPS
# ============================================================

def prepare_fact_sales(
    dataframe: pd.DataFrame,
    engine: Engine,
) -> pd.DataFrame:
    """
    Convert source-system business IDs into warehouse surrogate keys.

    Source sales data contains:
    - customer_id
    - product_id
    - location_id
    - channel_id
    - order_date

    warehouse.fact_sales requires:
    - customer_key
    - product_key
    - location_key
    - channel_key
    - date_key
    """

    sales = dataframe.copy()

    required_columns = {
        "order_id",
        "customer_id",
        "product_id",
        "location_id",
        "channel_id",
        "order_date",
    }

    missing_columns = required_columns - set(sales.columns)

    if missing_columns:
        raise ValueError(
            "fact_sales source data is missing columns: "
            f"{sorted(missing_columns)}"
        )

    # --------------------------------------------------------
    # Normalize business-key data types before joining
    # --------------------------------------------------------

    sales["customer_id"] = (
        sales["customer_id"]
        .astype(str)
        .str.strip()
    )

    sales["product_id"] = pd.to_numeric(
        sales["product_id"],
        errors="coerce",
    )

    sales["location_id"] = pd.to_numeric(
        sales["location_id"],
        errors="coerce",
    )

    sales["channel_id"] = pd.to_numeric(
        sales["channel_id"],
        errors="coerce",
    )

    sales["order_date"] = pd.to_datetime(
        sales["order_date"],
        errors="coerce",
    )

    # --------------------------------------------------------
    # Read dimension lookup tables
    # --------------------------------------------------------

    customer_lookup = pd.read_sql(
        """
        SELECT
            customer_id,
            customer_key
        FROM warehouse.dim_customer
        WHERE is_current = TRUE
          AND is_deleted = FALSE
        """,
        engine,
    )

    product_lookup = pd.read_sql(
        """
        SELECT
            product_id,
            product_key
        FROM warehouse.dim_product
        WHERE is_current = TRUE
          AND is_deleted = FALSE
        """,
        engine,
    )

    location_lookup = pd.read_sql(
        """
        SELECT
            location_id,
            location_key
        FROM warehouse.dim_location
        """,
        engine,
    )

    channel_lookup = pd.read_sql(
        """
        SELECT
            channel_id,
            channel_key
        FROM warehouse.dim_channel
        """,
        engine,
    )

    # --------------------------------------------------------
    # Normalize lookup business-key types
    # --------------------------------------------------------

    customer_lookup["customer_id"] = (
        customer_lookup["customer_id"]
        .astype(str)
        .str.strip()
    )

    product_lookup["product_id"] = pd.to_numeric(
        product_lookup["product_id"],
        errors="coerce",
    )

    location_lookup["location_id"] = pd.to_numeric(
        location_lookup["location_id"],
        errors="coerce",
    )

    channel_lookup["channel_id"] = pd.to_numeric(
        channel_lookup["channel_id"],
        errors="coerce",
    )

    # --------------------------------------------------------
    # Perform business-key to surrogate-key lookups
    # --------------------------------------------------------

    sales = sales.merge(
        customer_lookup,
        on="customer_id",
        how="left",
        validate="many_to_one",
    )

    sales = sales.merge(
        product_lookup,
        on="product_id",
        how="left",
        validate="many_to_one",
    )

    sales = sales.merge(
        location_lookup,
        on="location_id",
        how="left",
        validate="many_to_one",
    )

    sales = sales.merge(
        channel_lookup,
        on="channel_id",
        how="left",
        validate="many_to_one",
    )

    # YYYYMMDD warehouse date key
    sales["date_key"] = (
        sales["order_date"]
        .dt.strftime("%Y%m%d")
    )

    sales["date_key"] = pd.to_numeric(
        sales["date_key"],
        errors="coerce",
    )

    # --------------------------------------------------------
    # Validate lookup results
    # --------------------------------------------------------

    surrogate_key_columns = [
        "customer_key",
        "product_key",
        "location_key",
        "channel_key",
        "date_key",
    ]

    missing_lookup_mask = sales[
        surrogate_key_columns
    ].isna().any(axis=1)

    missing_lookup_count = int(
        missing_lookup_mask.sum()
    )

    if missing_lookup_count > 0:
        sample_failures = sales.loc[
            missing_lookup_mask,
            [
                "order_id",
                "customer_id",
                "product_id",
                "location_id",
                "channel_id",
            ],
        ].head(10)

        raise ValueError(
            f"{missing_lookup_count} fact_sales rows could not "
            "be matched to warehouse dimensions.\n"
            f"Sample unmatched records:\n{sample_failures}"
        )

    # --------------------------------------------------------
    # Keep only warehouse.fact_sales columns
    # --------------------------------------------------------

    warehouse_columns = [
        "order_id",
        "customer_key",
        "product_key",
        "location_key",
        "channel_key",
        "date_key",
        "quantity",
        "unit_price",
        "discount",
        "total_amount",
    ]

    fact_sales = sales[
        warehouse_columns
    ].copy()

    integer_columns = [
        "order_id",
        "customer_key",
        "product_key",
        "location_key",
        "channel_key",
        "date_key",
        "quantity",
    ]

    for column in integer_columns:
        fact_sales[column] = pd.to_numeric(
            fact_sales[column],
            errors="raise",
        ).astype("int64")

    print(
        f"Resolved surrogate keys for "
        f"{len(fact_sales):,} sales rows."
    )

    return fact_sales

# ============================================================
# MAIN PUBLIC LOAD FUNCTION
# ============================================================

def load_dataframe(
    df: pd.DataFrame,
    table_name: str,
) -> int:
    """
    Load one transformed DataFrame into PostgreSQL.

    Historical SCD Type 2 tables:
    - dim_customer
    - dim_product

    Standard incremental tables:
    - dim_location
    - dim_channel
    - fact_sales

    Returns
    -------
    Number of inserted or newly-versioned rows.
    """

    start_time = datetime.now()

    rows_loaded = 0
    rows_skipped = 0

    print(
        f"Loading data into "
        f"warehouse.{table_name}..."
    )

    try:
        # ----------------------------------------------------
        # Validate input
        # ----------------------------------------------------

        validate_identifier(
            table_name
        )

        if table_name not in TABLE_KEYS:
            raise ValueError(
                f"No business key configured "
                f"for table: {table_name}"
            )

        if not isinstance(df, pd.DataFrame):
            raise TypeError(
                "df must be a pandas DataFrame."
            )

        business_key = TABLE_KEYS[
            table_name
        ]

        validate_identifier(
            business_key
        )

        # ----------------------------------------------------
        # Empty DataFrame
        # ----------------------------------------------------

        if df.empty:
            end_time = datetime.now()

            write_etl_log(
                table_name=table_name,
                start_time=start_time,
                end_time=end_time,
                rows_loaded=0,
                rows_skipped=0,
                status="SUCCESS",
                error_message=None,
            )

            print(
                f"No rows received for "
                f"warehouse.{table_name}."
            )

            return 0

        engine = get_engine()
        if table_name == "fact_sales":
            df = prepare_fact_sales(
                dataframe=df,
                engine=engine,
            )

        # ----------------------------------------------------
        # Customer and product SCD Type 2 loading
        # ----------------------------------------------------

        if table_name in SCD2_TABLES:
            stats = load_historical_dimension(
                dataframe=df,
                table_name=table_name,
                business_key=business_key,
                engine=engine,
            )

            inserted = stats.get(
                "inserted",
                0,
            )

            updated = stats.get(
                "updated",
                0,
            )

            unchanged = stats.get(
                "unchanged",
                0,
            )

            deleted = stats.get(
                "deleted",
                0,
            )

            quarantined = stats.get(
                "quarantined",
                0,
            )

            rows_loaded = (
                inserted + updated
            )

            rows_skipped = (
                unchanged
                + deleted
                + quarantined
            )

            print(
                f"SCD2 results for "
                f"warehouse.{table_name}:"
            )

            print(
                f"Inserted: {inserted}"
            )

            print(
                f"Updated with history: {updated}"
            )

            print(
                f"Unchanged: {unchanged}"
            )

            print(
                f"Deleted: {deleted}"
            )

            print(
                f"Quarantined: {quarantined}"
            )

        # ----------------------------------------------------
        # Standard incremental loading
        # ----------------------------------------------------

        else:
            stats = load_incremental_table(
                dataframe=df,
                table_name=table_name,
                business_key=business_key,
                engine=engine,
            )

            rows_loaded = stats.get(
                "inserted",
                0,
            )

            rows_skipped = stats.get(
                "skipped",
                0,
            )

            print(
                f"Loaded {rows_loaded} new rows into "
                f"warehouse.{table_name}."
            )

            print(
                f"Skipped {rows_skipped} existing or "
                f"duplicate rows from "
                f"warehouse.{table_name}."
            )

        # ----------------------------------------------------
        # Success log
        # ----------------------------------------------------

        end_time = datetime.now()

        write_etl_log(
            table_name=table_name,
            start_time=start_time,
            end_time=end_time,
            rows_loaded=rows_loaded,
            rows_skipped=rows_skipped,
            status="SUCCESS",
            error_message=None,
        )

        return rows_loaded

    except Exception as error:
        # ----------------------------------------------------
        # Failure log
        # ----------------------------------------------------

        end_time = datetime.now()

        try:
            write_etl_log(
                table_name=table_name,
                start_time=start_time,
                end_time=end_time,
                rows_loaded=rows_loaded,
                rows_skipped=rows_skipped,
                status="FAILED",
                error_message=str(error),
            )

        except Exception as logging_error:
            print(
                "The ETL operation failed, and the failure "
                "could not be written to etl_run_log: "
                f"{logging_error}"
            )

        print(
            f"Failed loading warehouse."
            f"{table_name}: {error}"
        )

        raise