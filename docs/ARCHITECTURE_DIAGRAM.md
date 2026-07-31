# Customer 360 Analytics Warehouse

## End-to-End Data Flow

```text
                    CUSTOMER 360 ANALYTICS WAREHOUSE

                 +-------------------------------+
                 |        Source CSV Files       |
                 |-------------------------------|
                 | customers.csv                |
                 | products.csv                 |
                 | locations.csv               |
                 | channels.csv                |
                 | sales.csv                   |
                 +---------------+--------------+
                                 |
                                 v
                      +--------------------+
                      |   Extract Module   |
                      +--------------------+
                                 |
                                 v
                      +--------------------+
                      | Transform Module   |
                      |--------------------|
                      | Clean Data         |
                      | Standardize Names  |
                      | Validate Types     |
                      | Remove Duplicates  |
                      +--------------------+
                                 |
                                 v
                      +--------------------+
                      |   Load Module      |
                      |--------------------|
                      | PostgreSQL         |
                      | Duplicate Check    |
                      | Incremental Load   |
                      | ETL Logging        |
                      +--------------------+
                                 |
                                 v
                  +-------------------------------+
                  | PostgreSQL Data Warehouse     |
                  |-------------------------------|
                  | dim_customer                  |
                  | dim_product                   |
                  | dim_location                  |
                  | dim_channel                   |
                  | fact_sales                    |
                  +-------------------------------+
                                 |
                                 v
                  +-------------------------------+
                  | Business SQL Analytics        |
                  |-------------------------------|
                  | Total Revenue                 |
                  | Total Orders                  |
                  | Average Order Value           |
                  | Top Customers                 |
                  | Revenue by Category           |
                  | Revenue by Sales Channel      |
                  +-------------------------------+
```