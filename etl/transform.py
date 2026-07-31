"""
Transform Module
Customer 360 Analytics Warehouse
"""

import pandas as pd


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize column names before validation.

    Example:
    Customer ID -> customer_id
    """
    print("Standardizing column names...")

    df = df.copy()

    df.columns = (
        df.columns
        .str.lower()
        .str.strip()
        .str.replace(" ", "_", regex=False)
    )

    return df


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove duplicate rows and reject records only when
    essential identifier columns are missing.
    """
    print("Cleaning data...")

    df = df.copy()

    # Remove exact duplicate rows
    df = df.drop_duplicates()

    # Each CSV has one main business identifier.
    possible_identifier_columns = [
        "customer_id",
        "product_id",
        "location_id",
        "channel_id",
        "order_id",
    ]

    required_columns = [
        column
        for column in possible_identifier_columns
        if column in df.columns
    ]

    # Do not remove rows because optional fields such as
    # effective_to are empty.
    if required_columns:
        df = df.dropna(subset=required_columns)

    return df


def transform(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run the complete transformation process.
    """
    df = standardize_columns(df)
    df = clean_dataframe(df)

    return df