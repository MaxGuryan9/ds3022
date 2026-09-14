# Transforming Data with Python

## Raw Python scripts

Standalone scripts that load and explore data directly against DuckDB, no
modeling framework involved — [`import.py`](import.py) pulls the raw NYC
yellow taxi parquet into a local `trips.duckdb` table, and
[`longtrips.py`](longtrips.py) queries that table to compare mean vs. median
trip-distance cutoffs.

## dbt modeling

A proper [`dbt`](dbt/) project layered on top of the same taxi data: staged,
tested models built up in stages across the course (see `dbt/models/` for
what's live and `dbt/future/` for what's next).
