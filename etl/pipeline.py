"""
ETL Pipeline
Customer 360 Analytics Warehouse
"""

from etl.extract import (
    extract_customers,
    extract_products,
    extract_locations,
    extract_channels,
    extract_sales,
)

from etl.transform import transform
from etl.load import load_dataframe


def run_pipeline():
    print("=" * 50)
    print("Starting Customer 360 ETL Pipeline")
    print("=" * 50)

    datasets = {
        "dim_customer": extract_customers(),
        "dim_product": extract_products(),
        "dim_location": extract_locations(),
        "dim_channel": extract_channels(),
        "fact_sales": extract_sales(),
    }

    for table_name, dataframe in datasets.items():
        print(f"\nProcessing {table_name}...")

        transformed_dataframe = transform(dataframe)

        load_dataframe(
            df=transformed_dataframe,
            table_name=table_name,
        )

    print("\n" + "=" * 50)
    print("Customer 360 ETL Pipeline completed successfully")
    print("=" * 50)


if __name__ == "__main__":
    run_pipeline()