from __future__ import annotations

import random
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

RANDOM_SEED = 42

CUSTOMER_COUNT = 25_000
PRODUCT_COUNT = 2_000
LOCATION_COUNT = 500
CHANNEL_COUNT = 5
SALES_COUNT = 400_000


random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_FOLDER = PROJECT_ROOT / "data"

DATA_FOLDER.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# REFERENCE VALUES
# ============================================================

FIRST_NAMES = [
    "John",
    "Sarah",
    "Michael",
    "Emily",
    "David",
    "Jessica",
    "Daniel",
    "Ashley",
    "James",
    "Amanda",
    "Robert",
    "Priya",
    "Rahul",
    "Nithya",
    "Arjun",
    "Sophia",
    "Liam",
    "Olivia",
    "Noah",
    "Emma",
]

LAST_NAMES = [
    "Smith",
    "Johnson",
    "Brown",
    "Davis",
    "Wilson",
    "Miller",
    "Anderson",
    "Thomas",
    "Taylor",
    "Moore",
    "Patel",
    "Reddy",
    "Sharma",
    "Kumar",
    "Singh",
]

CITIES = [
    ("Dayton", "Ohio", "USA", "Midwest"),
    ("Columbus", "Ohio", "USA", "Midwest"),
    ("Austin", "Texas", "USA", "South"),
    ("Dallas", "Texas", "USA", "South"),
    ("Seattle", "Washington", "USA", "West"),
    ("San Francisco", "California", "USA", "West"),
    ("Chicago", "Illinois", "USA", "Midwest"),
    ("New York", "New York", "USA", "Northeast"),
    ("Boston", "Massachusetts", "USA", "Northeast"),
    ("Atlanta", "Georgia", "USA", "South"),
]

CATEGORIES = [
    ("Electronics", "Laptops"),
    ("Electronics", "Monitors"),
    ("Electronics", "Accessories"),
    ("Home", "Furniture"),
    ("Home", "Kitchen"),
    ("Office", "Supplies"),
    ("Sports", "Fitness"),
    ("Clothing", "Men"),
    ("Clothing", "Women"),
    ("Beauty", "Personal Care"),
]

BRANDS = [
    "Apple",
    "Dell",
    "Samsung",
    "Logitech",
    "Sony",
    "HP",
    "Lenovo",
    "Nike",
    "Adidas",
    "Generic",
]

CHANNELS = [
    ("4001", "Website", "Online", "Web"),
    ("4002", "Mobile App", "Online", "Mobile"),
    ("4003", "Marketplace", "Partner", "Marketplace"),
    ("4004", "Retail Store", "Offline", "Store"),
    ("4005", "Partner Store", "Partner", "Store"),
]


# ============================================================
# CUSTOMER GENERATION
# ============================================================

def generate_customers() -> pd.DataFrame:
    customer_ids = [
        str(100000 + index)
        for index in range(CUSTOMER_COUNT)
    ]

    first_names = np.random.choice(
        FIRST_NAMES,
        CUSTOMER_COUNT,
    )

    last_names = np.random.choice(
        LAST_NAMES,
        CUSTOMER_COUNT,
    )

    names = [
        f"{first} {last}"
        for first, last in zip(
            first_names,
            last_names,
        )
    ]

    cities = np.random.choice(
        [city[0] for city in CITIES],
        CUSTOMER_COUNT,
    )

    states = []

    for city in cities:
        city_record = next(
            item
            for item in CITIES
            if item[0] == city
        )

        states.append(
            city_record[1]
        )

    signup_dates = pd.to_datetime(
        np.random.choice(
            pd.date_range(
                "2020-01-01",
                "2026-06-30",
                freq="D",
            ),
            CUSTOMER_COUNT,
        )
    )

    dataframe = pd.DataFrame(
        {
            "customer_id": customer_ids,
            "customer_name": names,
            "email": [
                f"{name.lower().replace(' ', '.')}{index}@example.com"
                for index, name in enumerate(names)
            ],
            "phone": [
                f"937-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
                for _ in range(CUSTOMER_COUNT)
            ],
            "address": [
                f"{random.randint(100, 9999)} Main Street"
                for _ in range(CUSTOMER_COUNT)
            ],
            "city": cities,
            "state": states,
            "country": "USA",
            "customer_segment": np.random.choice(
                [
                    "Consumer",
                    "Small Business",
                    "Enterprise",
                ],
                CUSTOMER_COUNT,
                p=[
                    0.70,
                    0.20,
                    0.10,
                ],
            ),
            "loyalty_tier": np.random.choice(
                [
                    "Bronze",
                    "Silver",
                    "Gold",
                    "Platinum",
                ],
                CUSTOMER_COUNT,
                p=[
                    0.50,
                    0.30,
                    0.15,
                    0.05,
                ],
            ),
            "signup_date": signup_dates,
            "source_system": "CRM",
        }
    )

    return dataframe


# ============================================================
# PRODUCT GENERATION
# ============================================================

def generate_products() -> pd.DataFrame:
    products = []

    for index in range(PRODUCT_COUNT):
        category, subcategory = random.choice(
            CATEGORIES
        )

        brand = random.choice(
            BRANDS
        )

        unit_cost = round(
            random.uniform(
                5,
                1200,
            ),
            2,
        )

        markup = random.uniform(
            1.10,
            1.80,
        )

        selling_price = round(
            unit_cost * markup,
            2,
        )

        products.append(
            {
                "product_id": 200000 + index,
                "product_name": (
                    f"{brand} {subcategory} "
                    f"Model {index + 1}"
                ),
                "category": category,
                "subcategory": subcategory,
                "brand": brand,
                "supplier": f"{brand} Supplier",
                "unit_cost": unit_cost,
                "selling_price": selling_price,
                "source_system": "PRODUCT_SYSTEM",
            }
        )

    return pd.DataFrame(
        products
    )


# ============================================================
# LOCATION GENERATION
# ============================================================

def generate_locations() -> pd.DataFrame:
    locations = []

    for index in range(LOCATION_COUNT):
        city, state, country, region = random.choice(
            CITIES
        )

        locations.append(
            {
                "location_id": 300000 + index,
                "country": country,
                "state": state,
                "city": city,
                "postal_code": str(
                    random.randint(
                        10000,
                        99999,
                    )
                ),
                "region": region,
                "source_system": "LOCATION_SYSTEM",
            }
        )

    return pd.DataFrame(
        locations
    )

def generate_channels() -> pd.DataFrame:
    """
    Create the five sales channels used by the Customer 360 warehouse.

    Channel IDs are integers because warehouse.dim_channel.channel_id
    is an INTEGER column.
    """

    channels = pd.DataFrame(
        [
            {
                "channel_id": 4001,
                "channel_name": "Website",
                "channel_type": "Digital",
                "platform": "Web",
                "source_system": "CHANNEL_SYSTEM",
            },
            {
                "channel_id": 4002,
                "channel_name": "Mobile App",
                "channel_type": "Digital",
                "platform": "Mobile",
                "source_system": "CHANNEL_SYSTEM",
            },
            {
                "channel_id": 4003,
                "channel_name": "Retail Store",
                "channel_type": "Physical",
                "platform": "Store",
                "source_system": "CHANNEL_SYSTEM",
            },
            {
                "channel_id": 4004,
                "channel_name": "Marketplace",
                "channel_type": "Digital",
                "platform": "Marketplace",
                "source_system": "CHANNEL_SYSTEM",
            },
            {
                "channel_id": 4005,
                "channel_name": "Partner Store",
                "channel_type": "Partner",
                "platform": "Partner",
                "source_system": "CHANNEL_SYSTEM",
            },
        ]
    )

    return channels
# ============================================================
# CHANNEL GENERATION
# ============================================================

def generate_sales(
    customers: pd.DataFrame,
    products: pd.DataFrame,
    locations: pd.DataFrame,
    channels: pd.DataFrame,
) -> pd.DataFrame:
    """
    Generate 400,000 sales transactions.

    The function receives the generated dimension DataFrames so every
    foreign key in the sales data matches a real customer, product,
    location, and channel.

    order_id is numeric because warehouse.fact_sales.order_id is INTEGER.
    """

    # ---------------------------------------------------------
    # Read valid IDs from the generated dimension DataFrames
    # ---------------------------------------------------------

    customer_ids = customers["customer_id"].to_numpy()
    product_ids = products["product_id"].to_numpy()
    location_ids = locations["location_id"].to_numpy()
    channel_ids = channels["channel_id"].to_numpy()

    # ---------------------------------------------------------
    # Generate numeric order IDs
    # ---------------------------------------------------------

    order_ids = np.arange(
        1_000_000_001,
        1_000_000_001 + SALES_COUNT,
        dtype=np.int64,
    )

    # ---------------------------------------------------------
    # Generate transaction dates
    # ---------------------------------------------------------

    start_date = pd.Timestamp("2023-01-01")
    end_date = pd.Timestamp("2025-12-31")

    number_of_days = (end_date - start_date).days + 1

    order_dates = start_date + pd.to_timedelta(
        np.random.randint(
            0,
            number_of_days,
            size=SALES_COUNT,
        ),
        unit="D",
    )

    # ---------------------------------------------------------
    # Generate transaction measures
    # ---------------------------------------------------------

    quantities = np.random.randint(
        1,
        6,
        size=SALES_COUNT,
    )

    unit_prices = np.round(
        np.random.uniform(
            10.00,
            2500.00,
            size=SALES_COUNT,
        ),
        2,
    )

    discounts = np.random.choice(
        [0.00, 0.05, 0.10, 0.15, 0.20],
        size=SALES_COUNT,
        p=[0.40, 0.20, 0.20, 0.10, 0.10],
    )

    discounts = np.round(discounts, 2)

    total_amounts = np.round(
        quantities * unit_prices * (1 - discounts),
        2,
    )

    # ---------------------------------------------------------
    # Build the sales DataFrame
    # ---------------------------------------------------------

    sales = pd.DataFrame(
        {
            "order_id": order_ids,
            "customer_id": np.random.choice(
                customer_ids,
                size=SALES_COUNT,
            ),
            "product_id": np.random.choice(
                product_ids,
                size=SALES_COUNT,
            ),
            "location_id": np.random.choice(
                location_ids,
                size=SALES_COUNT,
            ),
            "channel_id": np.random.choice(
                channel_ids,
                size=SALES_COUNT,
            ),
            "order_date": order_dates,
            "quantity": quantities,
            "unit_price": unit_prices,
            "discount": discounts,
            "total_amount": total_amounts,
            "source_system": "SALES_SYSTEM",
        }
    )

    return sales

# ============================================================
# MAIN EXECUTION
# ============================================================

def main() -> None:
    print(
        "Generating large Customer 360 dataset..."
    )

    customers = generate_customers()

    products = generate_products()

    locations = generate_locations()

    channels = generate_channels()

    sales = generate_sales(
        customers=customers,
        products=products,
        locations=locations,
        channels=channels,
    )

    customers.to_csv(
        DATA_FOLDER / "customers.csv",
        index=False,
    )

    products.to_csv(
        DATA_FOLDER / "products.csv",
        index=False,
    )

    locations.to_csv(
        DATA_FOLDER / "locations.csv",
        index=False,
    )

    channels.to_csv(
        DATA_FOLDER / "channels.csv",
        index=False,
    )

    sales.to_csv(
        DATA_FOLDER / "sales.csv",
        index=False,
    )

    print(
        "Dataset generation completed."
    )

    print(
        f"Customers: {len(customers):,}"
    )

    print(
        f"Products: {len(products):,}"
    )

    print(
        f"Locations: {len(locations):,}"
    )

    print(
        f"Channels: {len(channels):,}"
    )

    print(
        f"Sales: {len(sales):,}"
    )


if __name__ == "__main__":
    main()