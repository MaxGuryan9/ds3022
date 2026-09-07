import pandas as pd
import polars as pl

url = "https://s3.amazonaws.com/uvasds-systems/data/FLIGHT_LOGS.csv"

# pandas
df_pd = pd.read_csv(url)
print(df_pd.head())

# polars
df_pl = pl.read_csv(url)
print(df_pl.head())

print("\nSchema:")
for name, dtype in df_pl.schema.items():
    print(f"  {name}: {dtype}")


