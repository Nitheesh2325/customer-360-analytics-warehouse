-- ==========================================
-- Sample Data - Customer Dimension
-- ==========================================

INSERT INTO warehouse.dim_customer
(
    customer_id,
    customer_name,
    email,
    phone,
    address,
    city,
    state,
    country,
    customer_segment,
    loyalty_tier,
    signup_date,
    row_hash,
    effective_from,
    effective_to,
    is_current,
    source_system
)
VALUES
(1001,'John Smith','john.smith@email.com','555-1001','123 Main St','Dallas','Texas','USA','Retail','Gold','2023-01-15','hash001',CURRENT_TIMESTAMP,NULL,TRUE,'CRM'),

(1002,'Sarah Johnson','sarah.j@email.com','555-1002','456 Oak Ave','Austin','Texas','USA','Retail','Silver','2023-02-10','hash002',CURRENT_TIMESTAMP,NULL,TRUE,'CRM'),

(1003,'Michael Brown','michael.b@email.com','555-1003','789 Pine Rd','Phoenix','Arizona','USA','Corporate','Gold','2022-11-05','hash003',CURRENT_TIMESTAMP,NULL,TRUE,'CRM'),

(1004,'Emily Davis','emily.d@email.com','555-1004','147 Cedar Ln','Miami','Florida','USA','Retail','Bronze','2024-01-18','hash004',CURRENT_TIMESTAMP,NULL,TRUE,'CRM'),

(1005,'David Wilson','david.w@email.com','555-1005','963 Lake Dr','Seattle','Washington','USA','Corporate','Platinum','2021-09-20','hash005',CURRENT_TIMESTAMP,NULL,TRUE,'CRM');



-- ==========================================
-- Sample Data - Product Dimension
-- ==========================================

INSERT INTO warehouse.dim_product
(
    product_id,
    product_name,
    category,
    subcategory,
    brand,
    supplier,
    unit_cost,
    selling_price,
    row_hash,
    source_system
)
VALUES
(2001, 'Apple MacBook Pro 14', 'Electronics', 'Laptops', 'Apple', 'TechSupply Inc', 1450.00, 1899.00, 'prodhash001', 'PRODUCT_SYSTEM'),

(2002, 'Dell XPS 15', 'Electronics', 'Laptops', 'Dell', 'Global Devices LLC', 1200.00, 1599.00, 'prodhash002', 'PRODUCT_SYSTEM'),

(2003, 'Logitech MX Master 3S', 'Electronics', 'Accessories', 'Logitech', 'OfficeTech Supply', 65.00, 99.99, 'prodhash003', 'PRODUCT_SYSTEM'),

(2004, 'Samsung 49 Inch Monitor', 'Electronics', 'Monitors', 'Samsung', 'DisplayWorld Inc', 950.00, 1299.00, 'prodhash004', 'PRODUCT_SYSTEM'),

(2005, 'Mechanical Keyboard', 'Electronics', 'Accessories', 'Keychron', 'OfficeTech Supply', 70.00, 119.00, 'prodhash005', 'PRODUCT_SYSTEM');

-- ==========================================
-- Sample Data - Location Dimension
-- ==========================================

INSERT INTO warehouse.dim_location
(
    location_id,
    country,
    state,
    city,
    postal_code,
    region,
    row_hash,
    source_system
)
VALUES
(3001, 'USA', 'Texas', 'Dallas', '75201', 'South', 'lochash001', 'LOCATION_SYSTEM'),
(3002, 'USA', 'Texas', 'Austin', '73301', 'South', 'lochash002', 'LOCATION_SYSTEM'),
(3003, 'USA', 'Arizona', 'Phoenix', '85001', 'West', 'lochash003', 'LOCATION_SYSTEM'),
(3004, 'USA', 'Florida', 'Miami', '33101', 'South', 'lochash004', 'LOCATION_SYSTEM'),
(3005, 'USA', 'Washington', 'Seattle', '98101', 'West', 'lochash005', 'LOCATION_SYSTEM');

-- ==========================================
-- Sample Data - Channel Dimension
-- ==========================================

INSERT INTO warehouse.dim_channel
(
    channel_id,
    channel_name,
    channel_type,
    platform,
    row_hash,
    source_system
)
VALUES
(4001, 'Website', 'Online', 'Web', 'channelhash001', 'SALES_SYSTEM'),
(4002, 'Mobile App', 'Online', 'Android', 'channelhash002', 'SALES_SYSTEM'),
(4003, 'Retail Store', 'Offline', 'Store', 'channelhash003', 'SALES_SYSTEM'),
(4004, 'Marketplace', 'Online', 'Amazon', 'channelhash004', 'SALES_SYSTEM'),
(4005, 'Partner Store', 'Partner', 'Retail Partner', 'channelhash005', 'SALES_SYSTEM');

-- ==========================================
-- Sample Data - Date Dimension
-- ==========================================

INSERT INTO warehouse.dim_date
(
    date_key,
    full_date,
    day,
    month,
    month_name,
    quarter,
    year,
    week_number,
    day_name,
    is_weekend
)
VALUES
(20260101, '2026-01-01', 1, 1, 'January', 1, 2026, 1, 'Thursday', FALSE),
(20260102, '2026-01-02', 2, 1, 'January', 1, 2026, 1, 'Friday', FALSE),
(20260103, '2026-01-03', 3, 1, 'January', 1, 2026, 1, 'Saturday', TRUE),
(20260104, '2026-01-04', 4, 1, 'January', 1, 2026, 1, 'Sunday', TRUE),
(20260105, '2026-01-05', 5, 1, 'January', 1, 2026, 2, 'Monday', FALSE);


-- ==========================================
-- Sample Data - Sales Fact Table
-- ==========================================

INSERT INTO warehouse.fact_sales
(
    order_id,
    customer_key,
    product_key,
    location_key,
    channel_key,
    date_key,
    quantity,
    unit_price,
    discount,
    total_amount
)
VALUES
(5001, 1, 1, 1, 1, 20260101, 1, 1899.00, 100.00, 1799.00),
(5002, 2, 2, 2, 2, 20260102, 1, 1599.00, 50.00, 1549.00),
(5003, 3, 3, 3, 3, 20260103, 2, 99.99, 0.00, 199.98),
(5004, 4, 4, 4, 4, 20260104, 1, 1299.00, 150.00, 1149.00),
(5005, 5, 5, 5, 5, 20260105, 3, 119.00, 20.00, 337.00);