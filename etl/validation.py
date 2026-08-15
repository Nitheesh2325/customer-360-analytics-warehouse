"""Source-record validation used before Customer360 warehouse loading."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class RejectedRecord:
    raw_record: dict[str, Any]
    reason: str


FACT_REQUIRED_IDENTIFIERS = (
    "order_id",
    "customer_id",
    "product_id",
    "location_id",
    "channel_id",
    "order_date",
)


def validate_fact_records(
    dataframe: pd.DataFrame,
) -> tuple[pd.DataFrame, list[RejectedRecord]]:
    """Return valid facts and deterministic rejection reasons."""
    missing_columns = set(FACT_REQUIRED_IDENTIFIERS) - set(dataframe.columns)
    if missing_columns:
        raise ValueError(f"fact_sales source is missing columns: {sorted(missing_columns)}")

    valid_indexes: list[Any] = []
    rejected: list[RejectedRecord] = []
    for index, row in dataframe.iterrows():
        record = row.to_dict()
        reasons: list[str] = []

        for column in FACT_REQUIRED_IDENTIFIERS:
            value = record.get(column)
            if pd.isna(value) or str(value).strip() == "":
                reasons.append(f"missing required identifier: {column}")

        quantity = pd.to_numeric(record.get("quantity"), errors="coerce")
        unit_price = pd.to_numeric(record.get("unit_price"), errors="coerce")
        discount = pd.to_numeric(record.get("discount"), errors="coerce")
        total_amount = pd.to_numeric(record.get("total_amount"), errors="coerce")

        if pd.isna(quantity) or quantity <= 0 or float(quantity) % 1:
            reasons.append("quantity must be a positive integer")
        if pd.isna(unit_price) or unit_price < 0:
            reasons.append("unit_price must be non-negative")
        if pd.isna(discount) or not 0 <= discount <= 1:
            reasons.append("discount must be between 0 and 1")
        if pd.isna(total_amount) or total_amount < 0:
            reasons.append("total_amount must be non-negative")

        if not reasons:
            try:
                expected_total = (
                    Decimal(str(quantity))
                    * Decimal(str(unit_price))
                    * (Decimal("1") - Decimal(str(discount)))
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
                actual_total = Decimal(str(total_amount)).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_EVEN
                )
            except InvalidOperation:
                reasons.append("total_amount cannot be reconciled")
            else:
                if abs(actual_total - expected_total) > Decimal("0.01"):
                    reasons.append(
                        f"total_amount does not reconcile; expected {expected_total:.2f}"
                    )

        if reasons:
            rejected.append(RejectedRecord(record, "; ".join(reasons)))
        else:
            valid_indexes.append(index)

    return dataframe.loc[valid_indexes].copy(), rejected
