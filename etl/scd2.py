"""
SCD Type 2 / CDC Module
Customer 360 Analytics Warehouse

Purpose
-------
- Preserve historical versions of customer and product records.
- Insert new business keys.
- Expire the previous current version when tracked data changes.
- Insert a new current version after a change.
- Keep unchanged rows untouched.
- Support soft-delete CDC events when an operation column marks DELETE.
- Avoid PostgreSQL VARCHAR-versus-INTEGER comparison errors by converting
  incoming business keys to the reflected database column type.

Expected public function
------------------------
load_scd2_dimension(
    dataframe=df,
    table_name="dim_customer",
    business_key="customer_id",
    engine=engine,                 # optional
)

Returns
-------
{
    "inserted": int,
    "updated": int,
    "unchanged": int,
    "deleted": int,
    "quarantined": int
}
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import pandas as pd
from sqlalchemy import MetaData, Table, create_engine, select
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import NoSuchTableError

from etl.config import get_database_url


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_engine() -> Engine:
    """
    Create the PostgreSQL SQLAlchemy engine.

    Connection settings are loaded by etl.config from the environment or .env.
    """
    return create_engine(
        get_database_url(),
        pool_pre_ping=True,
    )


# ============================================================
# GENERAL HELPERS
# ============================================================

TECHNICAL_COLUMNS = {
    "customer_key",
    "product_key",
    "location_key",
    "channel_key",
    "sales_key",
    "row_hash",
    "effective_from",
    "effective_to",
    "is_current",
    "is_deleted",
    "created_at",
    "updated_at",
}

DELETE_OPERATION_VALUES = {
    "DELETE",
    "DELETED",
    "D",
    "REMOVE",
    "REMOVED",
}

OPERATION_COLUMNS = (
    "_operation",
    "operation",
    "change_type",
    "cdc_operation",
    "op",
)


def make_postgres_safe(value: Any) -> Any:
    """
    Convert pandas/numpy values into normal Python values accepted by psycopg2.
    """
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    if hasattr(value, "item"):
        try:
            return value.item()
        except (ValueError, TypeError):
            pass

    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()

    return value


def prepare_record(source_record: dict[str, Any]) -> dict[str, Any]:
    """
    Convert every value in one source record into a PostgreSQL-safe value.
    """
    return {
        column: make_postgres_safe(value)
        for column, value in source_record.items()
    }


def convert_to_database_type(value: Any, database_column: Any) -> Any:
    """
    Convert an incoming value to the Python type expected by the reflected
    PostgreSQL column.

    This is the critical fix for errors such as:
        character varying = integer

    Example:
        PostgreSQL column customer_id is VARCHAR.
        Incoming CSV value is integer 1001.
        This function converts 1001 to "1001".
    """
    value = make_postgres_safe(value)

    if value is None:
        return None

    try:
        python_type = database_column.type.python_type
    except (AttributeError, NotImplementedError):
        return value

    if python_type is str:
        return str(value)

    if python_type is int:
        if isinstance(value, str):
            value = value.strip()
        return int(value)

    if python_type is float:
        return float(value)

    if python_type is Decimal:
        return Decimal(str(value))

    if python_type is bool:
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"true", "1", "yes", "y"}:
                return True
            if normalized in {"false", "0", "no", "n"}:
                return False
        return bool(value)

    if python_type is datetime:
        return pd.to_datetime(value).to_pydatetime()

    if python_type is date:
        return pd.to_datetime(value).date()

    return value


def detect_operation(record: dict[str, Any]) -> str:
    """
    Return INSERT_UPDATE or DELETE based on an optional CDC operation column.
    """
    for column in OPERATION_COLUMNS:
        value = record.get(column)

        if value is not None:
            normalized = str(value).strip().upper()

            if normalized in DELETE_OPERATION_VALUES:
                return "DELETE"

    return "INSERT_UPDATE"


def build_row_hash(
    record: dict[str, Any],
    table_columns: set[str],
    business_key: str,
) -> str:
    """
    Create a stable SHA-256 hash from business attributes.

    Source-provided hashes are never trusted. The warehouse recomputes a stable
    hash from controlled business attributes on every load.
    """
    ignored_columns = TECHNICAL_COLUMNS | set(OPERATION_COLUMNS)

    hash_payload = {
        column: record.get(column)
        for column in sorted(table_columns)
        if (
            column not in ignored_columns
            and column != business_key
            and column in record
        )
    }

    serialized = json.dumps(
        hash_payload,
        sort_keys=True,
        default=str,
        separators=(",", ":"),
    )

    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def filter_record_for_table(
    record: dict[str, Any],
    dimension_table: Table,
) -> dict[str, Any]:
    """
    Keep only columns that physically exist in the destination table.

    Surrogate primary keys are omitted so PostgreSQL can generate them.
    """
    table_column_names = {column.name for column in dimension_table.columns}

    filtered: dict[str, Any] = {}

    for column_name, value in record.items():
        if column_name not in table_column_names:
            continue

        column = dimension_table.c[column_name]

        # Let SERIAL / IDENTITY / sequence-backed primary keys generate.
        if column.primary_key and (
            column.autoincrement is True
            or column.autoincrement == "auto"
            or column.default is not None
            or column.server_default is not None
        ):
            continue

        filtered[column_name] = make_postgres_safe(value)

    return filtered


# ============================================================
# OPTIONAL QUARANTINE AND CDC AUDIT
# ============================================================

def reflect_optional_table(
    engine: Engine,
    table_name: str,
) -> Table | None:
    """
    Reflect an optional warehouse table. Return None when it does not exist.
    """
    metadata = MetaData()

    try:
        return Table(
            table_name,
            metadata,
            schema="warehouse",
            autoload_with=engine,
        )
    except NoSuchTableError:
        return None


def quarantine_record(
    connection: Connection,
    rejected_table: Table | None,
    table_name: str,
    business_key: str,
    raw_record: dict[str, Any],
    rejection_reason: str,
) -> None:
    """
    Write a rejected source record when warehouse.rejected_records exists.
    """
    if rejected_table is None:
        return

    values: dict[str, Any] = {}

    available_columns = {
        column.name
        for column in rejected_table.columns
    }

    candidate_values = {
        "source_name": "Customer 360 CSV Source",
        "table_name": table_name,
        "business_key": str(raw_record.get(business_key, "MISSING")),
        "raw_record": json.loads(json.dumps(raw_record, default=str)),
        "rejection_reason": rejection_reason,
        "rejected_at": datetime.now(),
        "resolved": False,
    }

    for column_name, value in candidate_values.items():
        if column_name in available_columns:
            values[column_name] = value

    if values:
        connection.execute(
            rejected_table.insert().values(**values)
        )


def quarantine_record_independently(
    engine: Engine,
    table_name: str,
    business_key: str,
    raw_record: dict[str, Any],
    rejection_reason: str,
) -> None:
    """Commit a rejection separately so a failed dimension transaction cannot erase it."""
    rejected_table = reflect_optional_table(engine, "rejected_records")
    if rejected_table is None:
        return
    with engine.begin() as connection:
        quarantine_record(
            connection=connection,
            rejected_table=rejected_table,
            table_name=table_name,
            business_key=business_key,
            raw_record=raw_record,
            rejection_reason=rejection_reason,
        )


def write_cdc_audit(
    connection: Connection,
    audit_table: Table | None,
    table_name: str,
    business_key: str,
    business_key_value: Any,
    change_type: str,
    old_row_hash: str | None,
    new_row_hash: str | None,
) -> None:
    """
    Write a CDC audit record when an expected audit table exists.

    The function supports common audit column names and silently skips
    unsupported optional columns.
    """
    if audit_table is None:
        return

    available_columns = {
        column.name
        for column in audit_table.columns
    }

    candidate_values = {
        "table_name": table_name,
        "business_key": business_key,
        "business_key_value": str(business_key_value),
        "change_type": change_type,
        "old_row_hash": old_row_hash,
        "new_row_hash": new_row_hash,
        "changed_at": datetime.now(),
        "created_at": datetime.now(),
    }

    values = {
        column_name: value
        for column_name, value in candidate_values.items()
        if column_name in available_columns
    }

    if values:
        connection.execute(
            audit_table.insert().values(**values)
        )


# ============================================================
# MAIN SCD TYPE 2 / CDC FUNCTION
# ============================================================

def load_scd2_dimension(
    dataframe: pd.DataFrame,
    table_name: str,
    business_key: str,
    engine: Engine | None = None,
) -> dict[str, int]:
    """
    Load one historical dimension using SCD Type 2 behavior.

    Rules
    -----
    1. New business key:
       Insert one current row.

    2. Existing business key with unchanged row_hash:
       Leave the current row untouched.

    3. Existing business key with changed row_hash:
       Expire the old current row and insert a new current row.

    4. DELETE CDC operation:
       Expire the current row and mark it deleted.

    5. Missing business key:
       Quarantine the record when warehouse.rejected_records exists.

    Parameters
    ----------
    dataframe:
        Transformed pandas DataFrame.

    table_name:
        PostgreSQL dimension table name inside the warehouse schema.

    business_key:
        Natural key, such as customer_id or product_id.

    engine:
        Optional SQLAlchemy Engine. When omitted, this module creates one.

    Returns
    -------
    Dictionary containing inserted, updated, unchanged, deleted,
    and quarantined row counts.
    """
    if dataframe is None:
        raise ValueError("dataframe cannot be None.")

    if not isinstance(dataframe, pd.DataFrame):
        raise TypeError(
            "dataframe must be a pandas DataFrame."
        )

    if dataframe.empty:
        stats = {
            "inserted": 0,
            "updated": 0,
            "unchanged": 0,
            "deleted": 0,
            "quarantined": 0,
        }

        print(
            f"SCD2 load completed for {table_name}: "
            "0 inserted, 0 updated, 0 unchanged, "
            "0 deleted, 0 quarantined."
        )

        return stats

    if business_key not in dataframe.columns:
        raise ValueError(
            f"Incoming DataFrame for {table_name} is missing "
            f"business-key column: {business_key}"
        )

    active_engine = engine or get_engine()

    metadata = MetaData()

    dimension_table = Table(
        table_name,
        metadata,
        schema="warehouse",
        autoload_with=active_engine,
    )

    if business_key not in dimension_table.c:
        raise ValueError(
            f"warehouse.{table_name} is missing "
            f"business-key column: {business_key}"
        )

    table_column_names = {
        column.name
        for column in dimension_table.columns
    }

    required_scd2_columns = {
        "row_hash",
        "effective_from",
        "effective_to",
        "is_current",
    }

    missing_columns = (
        required_scd2_columns - table_column_names
    )

    if missing_columns:
        raise ValueError(
            f"warehouse.{table_name} is missing required "
            f"SCD2 columns: {sorted(missing_columns)}"
        )

    # Keep one incoming record per business key.
    working_dataframe = (
        dataframe
        .drop_duplicates(
            subset=[business_key],
            keep="last",
        )
        .copy()
    )

    stats = {
        "inserted": 0,
        "updated": 0,
        "unchanged": 0,
        "deleted": 0,
        "quarantined": 0,
    }

    rejected_table = reflect_optional_table(
        active_engine,
        "rejected_records",
    )

    audit_table = reflect_optional_table(
        active_engine,
        "cdc_audit_log",
    )

    if audit_table is None:
        audit_table = reflect_optional_table(
            active_engine,
            "cdc_audit",
        )

    business_key_column = dimension_table.c[business_key]

    with active_engine.begin() as connection:
        for _, source_row in working_dataframe.iterrows():
            raw_record = prepare_record(
                source_row.to_dict()
            )

            try:
                key_value = convert_to_database_type(
                    raw_record.get(business_key),
                    business_key_column,
                )

                raw_record[business_key] = key_value

                if (
                    key_value is None
                    or str(key_value).strip() == ""
                ):
                    quarantine_record(
                        connection=connection,
                        rejected_table=rejected_table,
                        table_name=table_name,
                        business_key=business_key,
                        raw_record=raw_record,
                        rejection_reason=(
                            f"Missing required business key: "
                            f"{business_key}"
                        ),
                    )

                    stats["quarantined"] += 1
                    continue

                operation = detect_operation(raw_record)

                new_row_hash = build_row_hash(
                    record=raw_record,
                    table_columns=table_column_names,
                    business_key=business_key,
                )

                # IMPORTANT:
                # key_value has already been converted to the exact Python
                # type expected by the reflected PostgreSQL column.
                current_row = connection.execute(
                    select(dimension_table)
                    .where(
                        business_key_column == key_value,
                        dimension_table.c.is_current.is_(True),
                    )
                    .limit(1)
                ).mappings().first()

                now = datetime.now()

                # ------------------------------------------------
                # CDC DELETE
                # ------------------------------------------------
                if operation == "DELETE":
                    if current_row is None:
                        stats["unchanged"] += 1
                        continue

                    delete_values: dict[str, Any] = {
                        "is_current": False,
                        "effective_to": now,
                    }

                    if "is_deleted" in table_column_names:
                        delete_values["is_deleted"] = True

                    if "updated_at" in table_column_names:
                        delete_values["updated_at"] = now

                    connection.execute(
                        dimension_table.update()
                        .where(
                            business_key_column == key_value,
                            dimension_table.c.is_current.is_(True),
                        )
                        .values(**delete_values)
                    )

                    write_cdc_audit(
                        connection=connection,
                        audit_table=audit_table,
                        table_name=table_name,
                        business_key=business_key,
                        business_key_value=key_value,
                        change_type="DELETE",
                        old_row_hash=current_row.get("row_hash"),
                        new_row_hash=None,
                    )

                    stats["deleted"] += 1
                    continue

                # ------------------------------------------------
                # NEW BUSINESS KEY
                # ------------------------------------------------
                if current_row is None:
                    insert_record = filter_record_for_table(
                        raw_record,
                        dimension_table,
                    )

                    insert_record["row_hash"] = new_row_hash
                    insert_record["effective_from"] = now
                    insert_record["effective_to"] = None
                    insert_record["is_current"] = True

                    if "is_deleted" in table_column_names:
                        insert_record["is_deleted"] = False

                    if "created_at" in table_column_names:
                        insert_record.setdefault(
                            "created_at",
                            now,
                        )

                    if "updated_at" in table_column_names:
                        insert_record["updated_at"] = now

                    connection.execute(
                        dimension_table.insert().values(
                            **insert_record
                        )
                    )

                    write_cdc_audit(
                        connection=connection,
                        audit_table=audit_table,
                        table_name=table_name,
                        business_key=business_key,
                        business_key_value=key_value,
                        change_type="INSERT",
                        old_row_hash=None,
                        new_row_hash=new_row_hash,
                    )

                    stats["inserted"] += 1
                    continue

                old_row_hash = current_row.get("row_hash")

                # ------------------------------------------------
                # UNCHANGED BUSINESS KEY
                # ------------------------------------------------
                if old_row_hash == new_row_hash:
                    stats["unchanged"] += 1
                    continue

                # ------------------------------------------------
                # CHANGED BUSINESS KEY: SCD TYPE 2
                # ------------------------------------------------
                expire_values: dict[str, Any] = {
                    "effective_to": now,
                    "is_current": False,
                }

                if "updated_at" in table_column_names:
                    expire_values["updated_at"] = now

                connection.execute(
                    dimension_table.update()
                    .where(
                        business_key_column == key_value,
                        dimension_table.c.is_current.is_(True),
                    )
                    .values(**expire_values)
                )

                new_version = filter_record_for_table(
                    raw_record,
                    dimension_table,
                )

                new_version["row_hash"] = new_row_hash
                new_version["effective_from"] = now
                new_version["effective_to"] = None
                new_version["is_current"] = True

                if "is_deleted" in table_column_names:
                    new_version["is_deleted"] = False

                if "created_at" in table_column_names:
                    new_version["created_at"] = now

                if "updated_at" in table_column_names:
                    new_version["updated_at"] = now

                connection.execute(
                    dimension_table.insert().values(
                        **new_version
                    )
                )

                write_cdc_audit(
                    connection=connection,
                    audit_table=audit_table,
                    table_name=table_name,
                    business_key=business_key,
                    business_key_value=key_value,
                    change_type="UPDATE",
                    old_row_hash=old_row_hash,
                    new_row_hash=new_row_hash,
                )

                stats["updated"] += 1

            except Exception as record_error:
                quarantine_record_independently(
                    engine=active_engine,
                    table_name=table_name,
                    business_key=business_key,
                    raw_record=raw_record,
                    rejection_reason=str(record_error),
                )

                stats["quarantined"] += 1

                # Raise the error so the pipeline does not falsely report success.
                raise

    print(
        f"SCD2 load completed for {table_name}: "
        f"{stats['inserted']} inserted, "
        f"{stats['updated']} updated, "
        f"{stats['unchanged']} unchanged, "
        f"{stats['deleted']} deleted, "
        f"{stats['quarantined']} quarantined."
    )

    return stats
