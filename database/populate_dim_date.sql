INSERT INTO warehouse.dim_date (
    date_key, full_date, day, month, month_name, quarter, year,
    week_number, day_name, is_weekend
)
SELECT
    TO_CHAR(calendar_date, 'YYYYMMDD')::INTEGER,
    calendar_date::DATE,
    EXTRACT(DAY FROM calendar_date)::SMALLINT,
    EXTRACT(MONTH FROM calendar_date)::SMALLINT,
    TO_CHAR(calendar_date, 'FMMonth'),
    EXTRACT(QUARTER FROM calendar_date)::SMALLINT,
    EXTRACT(YEAR FROM calendar_date)::SMALLINT,
    EXTRACT(WEEK FROM calendar_date)::SMALLINT,
    TO_CHAR(calendar_date, 'FMDay'),
    EXTRACT(ISODOW FROM calendar_date) IN (6, 7)
FROM GENERATE_SERIES(
    DATE '2023-01-01', DATE '2025-12-31', INTERVAL '1 day'
) AS dates(calendar_date)
ON CONFLICT (date_key) DO NOTHING;
