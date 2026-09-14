import os
import duckdb


url = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet"
db_path = os.path.join(os.path.dirname(__file__), "trips.duckdb")

# read remote parquet into new local table

with duckdb.connect(db_path) as con:
    con.execute(f"""
        CREATE OR REPLACE TABLE trips AS
        SELECT * FROM read_parquet('{url}')
    """)

    print(f"Loaded {con.execute('SELECT COUNT(*) FROM trips').fetchone()[0]} rows into {db_path}")
