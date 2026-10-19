from prefect import flow, task
from datetime import date
import httpx

BASE_URL = "https://data.gharchive.org/{day}-{hour}.json.gz"


@task
def build_hour_keys(start: date, days: int = 7) -> list[str]:
    """Return 'YYYY-MM-DD-H' keys for each hour in the window."""
    pass


@task(retries=3, retry_delay_seconds=10)
def count_events_for_hour(hour_key: str) -> dict[str, int]:
    """Stream one hourly file and return {event_type: count}. No raw JSON kept."""
    pass


@task
def combine_counts(hourly_counts: list[dict[str, int]]) -> dict[str, int]:
    """Sum per-hour counts into weekly totals."""
    pass


@task
def save_counts(totals: dict[str, int]) -> None:
    """Persist aggregated counts only."""
    pass


@flow
def gharchive_week_flow(start: date = date(2025, 1, 1), days: int = 7):
    """Week of GH Archive -> counts by event type."""
    pass


if __name__ == "__main__":
    gharchive_week_flow()
