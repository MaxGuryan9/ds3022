import os
import duckdb
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


db_path = os.path.join(os.path.dirname(__file__), "trips.duckdb")
out_path = os.path.join(os.path.dirname(__file__), "trip_distance_cutoffs.png")

# clip to a reasonable range for plotting -- a handful of extreme outliers
# otherwise stretch the x-axis and hide the shape of the distribution
MAX_DISTANCE = 20

with duckdb.connect(db_path) as con:
    mean_distance = con.execute("SELECT AVG(trip_distance) FROM trips").fetchone()[0]
    median_distance = con.execute(
        "SELECT MEDIAN(trip_distance) FROM trips"
    ).fetchone()[0]
    total = con.execute("SELECT COUNT(*) FROM trips").fetchone()[0]
    below_mean = con.execute(
        "SELECT COUNT(*) FROM trips WHERE trip_distance < ?", [mean_distance]
    ).fetchone()[0]
    below_median = con.execute(
        "SELECT COUNT(*) FROM trips WHERE trip_distance < ?", [median_distance]
    ).fetchone()[0]

    df = con.execute(
        "SELECT trip_distance FROM trips WHERE trip_distance BETWEEN 0 AND ?",
        [MAX_DISTANCE],
    ).df()

print(f"Mean trip distance:   {mean_distance:.2f} mi ({below_mean / total:.1%} of trips below it)")
print(f"Median trip distance: {median_distance:.2f} mi ({below_median / total:.1%} of trips below it)")

sns.set_theme(style="whitegrid")
fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)

cutoffs = [
    ("Cut at the mean", mean_distance, axes[0]),
    ("Cut at the median", median_distance, axes[1]),
]

for title, cutoff, ax in cutoffs:
    sns.histplot(df, x="trip_distance", bins=60, ax=ax, color="#4C72B0")
    ax.axvspan(0, cutoff, color="red", alpha=0.3, zorder=0)
    ax.axvline(cutoff, color="red", linestyle="--", linewidth=2)
    ax.set_title(f"{title}: {cutoff:.2f} mi")
    ax.set_xlabel("Trip distance (mi)")
    ax.set_xlim(0, MAX_DISTANCE)

axes[0].set_ylabel("Number of trips")

fig.suptitle("Yellow Taxi Trip Distance Distribution\nRed = trips that would be \"deleted\" below the cutoff")
fig.tight_layout()
fig.savefig(out_path, dpi=150)
print(f"Saved plot to {out_path}")
