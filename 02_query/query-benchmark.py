import time

import duckdb
import pandas as pd
import polars as pl

URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2026-01.parquet"


def bench_pandas(url):
    start = time.perf_counter()
    df = pd.read_parquet(url, columns=["fare_amount"])
    avg = df["fare_amount"].mean()
    elapsed = time.perf_counter() - start
    return avg, elapsed


def bench_polars(url):
    start = time.perf_counter()
    df = pl.read_parquet(url, columns=["fare_amount"])
    avg = df["fare_amount"].mean()
    elapsed = time.perf_counter() - start
    return avg, elapsed


def bench_duckdb(url):
    start = time.perf_counter()
    avg = duckdb.sql(
        f"SELECT AVG(fare_amount) FROM read_parquet('{url}')"
    ).fetchone()[0]
    elapsed = time.perf_counter() - start
    return avg, elapsed


def bench_pandas_groupby(url):
    start = time.perf_counter()
    df = pd.read_parquet(url, columns=["payment_type", "tip_amount"])
    result = df.groupby("payment_type")["tip_amount"].mean()
    elapsed = time.perf_counter() - start
    return result, elapsed


def bench_polars_groupby(url):
    start = time.perf_counter()
    df = pl.read_parquet(url, columns=["payment_type", "tip_amount"])
    result = df.group_by("payment_type").agg(pl.col("tip_amount").mean())
    elapsed = time.perf_counter() - start
    return result, elapsed


def bench_duckdb_groupby(url):
    start = time.perf_counter()
    result = duckdb.sql(
        f"""
        SELECT payment_type, AVG(tip_amount) AS avg_tip
        FROM read_parquet('{url}')
        GROUP BY payment_type
        ORDER BY payment_type
        """
    ).fetchall()
    elapsed = time.perf_counter() - start
    return result, elapsed


def main():
    results = {
        "pandas": bench_pandas(URL),
        "polars": bench_polars(URL),
        "duckdb": bench_duckdb(URL),
    }

    print("=== AVG(fare_amount) over full table ===")
    print(f"{'Library':<10} {'Avg fare_amount':>18} {'Elapsed (s)':>14}")
    for name, (avg, elapsed) in results.items():
        print(f"{name:<10} {avg:>18.4f} {elapsed:>14.4f}")

    groupby_results = {
        "pandas": bench_pandas_groupby(URL),
        "polars": bench_polars_groupby(URL),
        "duckdb": bench_duckdb_groupby(URL),
    }

    print("\n=== AVG(tip_amount) GROUP BY payment_type (narrow column projection) ===")
    print(f"{'Library':<10} {'Elapsed (s)':>14}")
    for name, (_, elapsed) in groupby_results.items():
        print(f"{name:<10} {elapsed:>14.4f}")


if __name__ == "__main__":
    main()
