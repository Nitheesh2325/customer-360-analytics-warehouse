BEGIN;

CREATE SCHEMA IF NOT EXISTS warehouse;

CREATE TABLE IF NOT EXISTS warehouse.bootstrap_metadata (
    bootstrap_version INTEGER PRIMARY KEY,
    initialized_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO warehouse.bootstrap_metadata (bootstrap_version)
VALUES (1)
ON CONFLICT (bootstrap_version) DO NOTHING;

CREATE TABLE IF NOT EXISTS warehouse.dim_customer (
    customer_key BIGSERIAL PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    customer_name VARCHAR(150),
    email VARCHAR(255),
    phone VARCHAR(30),
    address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    customer_segment VARCHAR(50),
    loyalty_tier VARCHAR(50),
    signup_date DATE,
    row_hash VARCHAR(64) NOT NULL,
    effective_from TIMESTAMP NOT NULL,
    effective_to TIMESTAMP,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    source_system VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_dim_customer_effective_period CHECK (
        (is_current AND effective_to IS NULL)
        OR (NOT is_current AND effective_to IS NOT NULL)
    )
);

CREATE TABLE IF NOT EXISTS warehouse.dim_product (
    product_key BIGSERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    product_name VARCHAR(150),
    category VARCHAR(100),
    subcategory VARCHAR(100),
    brand VARCHAR(100),
    supplier VARCHAR(100),
    unit_cost NUMERIC(12, 2),
    selling_price NUMERIC(12, 2),
    row_hash VARCHAR(64) NOT NULL,
    effective_from TIMESTAMP NOT NULL,
    effective_to TIMESTAMP,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    source_system VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_dim_product_effective_period CHECK (
        (is_current AND effective_to IS NULL)
        OR (NOT is_current AND effective_to IS NOT NULL)
    )
);

CREATE TABLE IF NOT EXISTS warehouse.dim_location (
    location_key BIGSERIAL PRIMARY KEY,
    location_id INTEGER NOT NULL UNIQUE,
    country VARCHAR(100),
    state VARCHAR(100),
    city VARCHAR(100),
    postal_code VARCHAR(20),
    region VARCHAR(100),
    row_hash VARCHAR(64),
    source_system VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS warehouse.dim_channel (
    channel_key BIGSERIAL PRIMARY KEY,
    channel_id INTEGER NOT NULL UNIQUE,
    channel_name VARCHAR(100),
    channel_type VARCHAR(100),
    platform VARCHAR(100),
    row_hash VARCHAR(64),
    source_system VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS warehouse.dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    day SMALLINT NOT NULL,
    month SMALLINT NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    quarter SMALLINT NOT NULL,
    year SMALLINT NOT NULL,
    week_number SMALLINT NOT NULL,
    day_name VARCHAR(20) NOT NULL,
    is_weekend BOOLEAN NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS warehouse.fact_sales (
    sales_key BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL UNIQUE,
    customer_key BIGINT NOT NULL REFERENCES warehouse.dim_customer(customer_key),
    product_key BIGINT NOT NULL REFERENCES warehouse.dim_product(product_key),
    location_key BIGINT NOT NULL REFERENCES warehouse.dim_location(location_key),
    channel_key BIGINT NOT NULL REFERENCES warehouse.dim_channel(channel_key),
    date_key INTEGER NOT NULL REFERENCES warehouse.dim_date(date_key),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(12, 2) NOT NULL CHECK (unit_price >= 0),
    discount NUMERIC(5, 2) NOT NULL DEFAULT 0 CHECK (discount BETWEEN 0 AND 1),
    total_amount NUMERIC(14, 2) NOT NULL CHECK (total_amount >= 0),
    source_system VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS warehouse.etl_run_log (
    run_id BIGSERIAL PRIMARY KEY,
    pipeline_name VARCHAR(150) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    rows_loaded INTEGER NOT NULL DEFAULT 0,
    rows_skipped INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL CHECK (status IN ('SUCCESS', 'FAILED')),
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS warehouse.cdc_audit_log (
    audit_id BIGSERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    business_key VARCHAR(100) NOT NULL,
    business_key_value VARCHAR(255) NOT NULL,
    change_type VARCHAR(20) NOT NULL CHECK (change_type IN ('INSERT', 'UPDATE', 'DELETE')),
    old_row_hash VARCHAR(64),
    new_row_hash VARCHAR(64),
    changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS warehouse.rejected_records (
    rejection_id BIGSERIAL PRIMARY KEY,
    source_name VARCHAR(150),
    table_name VARCHAR(100) NOT NULL,
    business_key VARCHAR(255),
    raw_record JSONB NOT NULL,
    rejection_reason TEXT NOT NULL,
    rejected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_dim_customer_current_business_key
    ON warehouse.dim_customer (customer_id) WHERE is_current;
CREATE UNIQUE INDEX IF NOT EXISTS ux_dim_product_current_business_key
    ON warehouse.dim_product (product_id) WHERE is_current;

CREATE INDEX IF NOT EXISTS ix_fact_sales_customer_key
    ON warehouse.fact_sales (customer_key);
CREATE INDEX IF NOT EXISTS ix_fact_sales_product_key
    ON warehouse.fact_sales (product_key);
CREATE INDEX IF NOT EXISTS ix_fact_sales_location_key
    ON warehouse.fact_sales (location_key);
CREATE INDEX IF NOT EXISTS ix_fact_sales_channel_key
    ON warehouse.fact_sales (channel_key);
CREATE INDEX IF NOT EXISTS ix_fact_sales_date_key
    ON warehouse.fact_sales (date_key);

COMMIT;
