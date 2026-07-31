"""
Extract Module
Customer 360 Analytics Warehouse
"""

import pandas as pd


def extract_customers():
    print("Extracting customer data...")
    return pd.read_csv("data/customers.csv")


def extract_products():
    print("Extracting product data...")
    return pd.read_csv("data/products.csv")


def extract_locations():
    print("Extracting location data...")
    return pd.read_csv("data/locations.csv")


def extract_channels():
    print("Extracting channel data...")
    return pd.read_csv("data/channels.csv")


def extract_sales():
    print("Extracting sales data...")
    return pd.read_csv("data/sales.csv")