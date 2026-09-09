# Week 2: Querying Data — Parquet vs. CSV

Setup: [**Install DuckDB**](https://github.com/uvasds-systems/ds3022/tree/main/01_data#install-duckdb).

When working with large datasets, the file format you choose has a big impact on speed, storage size, and how easy the data is to query. This week we compare two common formats: **CSV** and **Parquet**.

## CSV (Comma-Separated Values)

A plain-text, row-oriented format. Each line is a row; each value is separated by a comma.

**Pros**
- Human-readable — you can open it in any text editor
- Universally supported by nearly every tool and language
- Simple to create and debug

**Cons**
- No data types — everything is text until you parse it (dates, ints, floats all look the same)
- No compression — large file sizes on disk
- Slow to query — reading a single column still requires scanning every row and every column
- No embedded schema — column types must be inferred or specified separately

## Parquet

A binary, **columnar** format built for analytics workloads (used heavily in tools like Spark, DuckDB, and Pandas).

**Pros**
- Columnar storage — queries that only need a few columns can skip reading the rest, which is much faster
- Built-in compression — typically 5–10x smaller than the equivalent CSV
- Stores schema and data types with the file — no guessing on load
- Supports predicate pushdown — query engines can skip irrelevant chunks of data entirely

**Cons**
- Not human-readable — requires a library/tool to inspect
- Slightly more overhead to create for very small datasets
- Less universally supported outside the data/analytics ecosystem (e.g., you can't just open it in Excel)

## Rule of Thumb

- Use **CSV** for small datasets, quick sharing, or interoperability with non-technical tools.
- Use **Parquet** for larger datasets and any real analytical querying — it's faster, smaller, and preserves types.

## Samples

    https://s3.amazonaws.com/uvasds-systems/data/customers-2M.csv
    https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2026-01.parquet
