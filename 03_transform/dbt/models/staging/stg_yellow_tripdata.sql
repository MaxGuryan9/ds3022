-- Staging: light cleanup and standardization of raw parquet columns.
-- Materialized as a view — cheap, and dbt-duckdb reads parquet lazily.

with source as (
    select * from {{ source('raw', 'yellow_tripdata') }}
),

renamed as (
    select
        cast(vendorid as integer)              as vendor_id,
        cast(tpep_pickup_datetime as timestamp) as pickup_at,
        cast(tpep_dropoff_datetime as timestamp) as dropoff_at,
        cast(passenger_count as integer)        as passenger_count,
        cast(trip_distance as double)           as trip_distance_miles,
        cast(pulocationid as integer)           as pickup_location_id,
        cast(dolocationid as integer)           as dropoff_location_id,
        cast(payment_type as integer)           as payment_type_code,
        cast(fare_amount as double)             as fare_amount,
        cast(tip_amount as double)              as tip_amount,
        cast(tolls_amount as double)            as tolls_amount,
        cast(total_amount as double)            as total_amount
    from source
)

select *
from renamed
where
    -- filter out the well-known TLC data-quality junk before it
    -- propagates downstream
    pickup_at is not null
    and dropoff_at is not null
    and dropoff_at > pickup_at
    and trip_distance_miles > 0
    and fare_amount > 0
    and passenger_count > 0
