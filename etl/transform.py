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
    Remove exact duplicate rows. Loader-specific validation handles
    missing or invalid identifiers so rejected records remain observable.
    """
    print("Cleaning data...")

    df = df.copy()

    # Remove exact duplicate rows
    df = df.drop_duplicates()

    return df


def transform(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run the complete transformation process.
    """
    df = standardize_columns(df)
    df = clean_dataframe(df)

    return df
