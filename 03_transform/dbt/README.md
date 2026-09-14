# nyc_taxi_dbt

A minimal dbt project transforming NYC yellow taxi trip data, using
DuckDB as the adapter so it reads parquet directly over HTTPS — no
warehouse, download, or load step needed.

This project is being built up gradually across three classes. Right
now it contains just one model (Class 1 scope); the rest lives in
`future/` and gets folded in as we go.

## Layout

```
nyc_taxi_dbt/
├── dbt_project.yml
├── profiles.yml.example        # copy to ~/.dbt/profiles.yml
├── models/
│   └── staging/
│       ├── sources.yml               # points at the raw parquet (local or remote)
│       └── stg_yellow_tripdata.sql   # cast/clean raw columns
└── future/                     # not yet wired into models/ — added in later classes
    ├── staging_schema_with_tests.yml
    └── marts/
        ├── fct_trips.sql
        ├── mart_daily_summary.sql
        └── schema.yml
```

## Setup

1. Install: `pip install dbt-duckdb`
2. Copy `profiles.yml.example` to `~/.dbt/profiles.yml`.
3. From the `nyc_taxi_dbt/` directory:

```bash
dbt debug        # confirm the connection
dbt run          # build stg_yellow_tripdata
```

4. Query the result:

```bash
duckdb nyc_taxi.duckdb -c "select * from stg_yellow_tripdata limit 10;"
```

No local data file to download — `sources.yml` points `external_location`
at TLC's public HTTPS parquet host, and DuckDB's `httpfs`/`parquet`
extensions stream it on demand. That same `external_location` key can
just as easily point at a local file path or an `s3://` URL — see the
comments in `sources.yml`.

## Class-by-class build-up

- **Class 1 (current):** `stg_yellow_tripdata` only — a `source()`
  reading raw parquet, cast/renamed columns, a `where` filter dropping
  bad rows. Materialized as a `view`.
- **Class 2:** add `fct_trips` (`future/marts/fct_trips.sql`), wired
  via `{{ ref() }}` to the staging model — introduces model lineage
  and derived columns. Also promote `future/staging_schema_with_tests.yml`
  into `models/staging/schema.yml` and add `fct_trips`'s tests, then
  run `dbt test`.
- **Class 3:** add `mart_daily_summary` (`future/marts/mart_daily_summary.sql`)
  for the daily-rollup aggregation layer, and uncomment the `marts:`
  block in `dbt_project.yml`.

## Model chain (end state, after Class 3)

`stg_yellow_tripdata` (view, cleans/casts raw parquet) →
`fct_trips` (table, adds duration/speed/tip_pct, drops bad durations) →
`mart_daily_summary` (table, daily aggregates for reporting)
