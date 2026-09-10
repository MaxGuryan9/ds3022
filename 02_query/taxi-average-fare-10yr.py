import pathlib

import duckdb
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

DB_PATH = pathlib.Path(__file__).parent / "yellow_tripdata.duckdb"
OUTPUT_PATH = pathlib.Path(__file__).parent / "taxi-average-fare-10yr.png"
BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{year}-{month:02d}.parquet"
START_YEAR = 2016
END_YEAR = 2025


def month_keys():
    for year in range(START_YEAR, END_YEAR + 1):
        for month in range(1, 13):
            yield year, month


def load_yellow_tripdata(con):
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS yellow_tripdata (
            year INTEGER,
            month INTEGER,
            fare_amount DOUBLE
        )
        """
    )
    loaded = {
        row[0]
        for row in con.execute(
            "SELECT DISTINCT year * 100 + month FROM yellow_tripdata"
        ).fetchall()
    }

    for year, month in month_keys():
        key = year * 100 + month
        if key in loaded:
            continue
        url = BASE_URL.format(year=year, month=month)
        try:
            con.execute(
                """
                INSERT INTO yellow_tripdata
                SELECT ? AS year, ? AS month, fare_amount
                FROM read_parquet(?)
                WHERE fare_amount > 0 AND fare_amount < 500
                """,
                [year, month, url],
            )
            print(f"Loaded {year}-{month:02d}")
        except duckdb.Error as exc:
            print(f"Skipping {year}-{month:02d}: {exc}")


def monthly_average_fare(con):
    df = con.execute(
        """
        SELECT year, month, AVG(fare_amount) AS avg_fare
        FROM yellow_tripdata
        GROUP BY year, month
        ORDER BY year, month
        """
    ).fetchdf()
    df["date"] = pd.to_datetime(dict(year=df["year"], month=df["month"], day=1))
    return df


def plot_average_fare(df):
    df = df.sort_values("date").reset_index(drop=True)
    df["smoothed_fare"] = df["avg_fare"].rolling(window=6, center=True, min_periods=1).mean()

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.lineplot(
        data=df, x="date", y="avg_fare", ax=ax,
        color="lightsteelblue", linewidth=1, label="Monthly average fare",
    )
    sns.lineplot(
        data=df, x="date", y="smoothed_fare", ax=ax,
        color="crimson", linewidth=2.5, label="6-month smoothed trend",
    )

    ax.set_title("NYC Yellow Taxi Average Fare by Month (2016-2025)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Average Fare ($)")
    fig.tight_layout()
    fig.savefig(OUTPUT_PATH, dpi=150)
    print(f"Saved plot to {OUTPUT_PATH}")


def main():
    con = duckdb.connect(str(DB_PATH))
    load_yellow_tripdata(con)
    df = monthly_average_fare(con)
    plot_average_fare(df)
    con.close()


if __name__ == "__main__":
    main()
