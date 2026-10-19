"""
Work with Claude Code (CC) to complete this prefect flow.

The best way to do this is to open CC in the root dir of this
project, and your prompt can reference @05_prefect/07_github_api_pagination.py
to ask for a plan for how to complete the steps. the instructors
inline comments already add to the prompt - i.e. to paginate over that
API endpoint for a certain number of pages, and to store the output
in a single duckdb table. Ask CC to enumerate the steps you will need
to do this, and REQUIRE it to work with you on each task, one by one.

Read what CC generates/suggests with each step, and ask yourself if you
understand the python it has generated. IF YOU DO NOT UNDERSTAND IT WELL,
this is your chance to learn a bit more python! Ask CC to explain the specific
lines that are unclear to you, and have a back and forth with CC until you
get a sense for what is going on. You know about loops, and you know about
fetching remote web content, and so the growth here is understanding how
to cycle through a series of related links to build up all 1000 records.
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
import duckdb
import httpx
from prefect import flow, task
from prefect.logging import get_run_logger
from prefect.task_runners import ThreadPoolTaskRunner


# commit history for the git/git repository
TOKEN = os.environ["GH_PAT"]
HEADERS = {"Authorization": f"Bearer {TOKEN}"}
URL = "https://api.github.com/repos/git/git/commits"
PER_PAGE = 100
PAGES = 10

# Prefect already puts a handler on the root logger, which makes
# logging.basicConfig() a silent no-op, so attach a file handler directly
log = logging.getLogger("github_pagination")
log.setLevel(logging.INFO)
handler = logging.FileHandler(Path(__file__).with_suffix(".log"))
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
log.addHandler(handler)

# ------ only one task ------
# create a single prefect task that loops through 10 pages
# of git/git commits and stores each one into a duckdb table.
# add more tasks and more data if you like, and do more with it.
# if successful you should have 1000 records in your db.

# local duckdb file, created if missing
conn = duckdb.connect("actions.duckdb")  

def flatten(c):
    """Pull the useful fields out of one nested commit dict into a flat dict."""
    return {
        "sha":         c["sha"],
        "author_name": c["commit"]["author"]["name"],
        "commit_date": c["commit"]["author"]["date"],
        "message":     c["commit"]["message"].splitlines()[0],  # first line only
        "gh_login":    (c.get("author") or {}).get("login"),    # None-safe
        "url":         c["html_url"],
    }

@task(name="ingest", log_prints=True, retries=3, retry_delay_seconds=5)
def ingest_data():
    # work with claude to fetch 100 records for each page
    # and pull 10 pages total. This could be done in series,
    # or if you want to look at previous prefect .map examples
    # you could pull some/all pages concurrently.
    #
    # for help with github api pagination see
    # https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api?apiVersion=2026-03-10
    #
    # httpx parses it into response.links. The "next" URL already includes 
    # per_page and page, so params are only needed on the first request. 
    # The loop ends when there is no "next" link (last page).

    # this task already comes with a name, retry settings, and anything
    # you print() is written to the log.
    # visit https://sds-prefect.pods.uvarc.io/v2/runs to review your flows

    # if you need to see a working example of this, see this file in this repo
    # 04_apis/05_pagination.py

    url = URL                        # start at the base endpoint
    params = {"per_page": PER_PAGE}  # only needed on the first request
    page = 1
    all_commits = []                 # collects commits from every page

    # keep going while GitHub gives us a next link AND we're under the page cap
    while url and page <= PAGES:
        try:
            response = httpx.get(url, headers=HEADERS, params=params)
            response.raise_for_status()
        except httpx.HTTPError as e:
            log.error(f"page {page} failed: {e}")
            raise                    # re-raise so Prefect's retries=3 kicks in
        commits = response.json()
        all_commits.extend(commits)  # add this page's 100 to the running list
        print(f"page {page}: {len(commits)} commits (total {len(all_commits)})")

        url = response.links.get("next", {}).get("url")  # None on the last page
        params = None                # next URL already has per_page & page
        page += 1

    rows = [flatten(c) for c in all_commits]

    try:
        # CREATE OR REPLACE = rerunning gives 1000 rows, not 2000, 3000...
        conn.execute("""
            CREATE OR REPLACE TABLE commits (
                sha         VARCHAR PRIMARY KEY,
                author_name VARCHAR,
                commit_date TIMESTAMPTZ,
                message     VARCHAR,
                gh_login    VARCHAR,
                url         VARCHAR
            )""")
        # one ? per column; each row dict -> tuple in the same column order
        conn.executemany("INSERT INTO commits VALUES (?, ?, ?, ?, ?, ?)",
                         [tuple(r.values()) for r in rows])
        log.info(f"inserted {len(rows)} rows into commits")
    except duckdb.Error as e:
        log.error(f"duckdb insert failed: {e}")
        raise

    return len(rows)


# name the flow something you can identify as yourself
@flow(name="rhk2dx-flow")
def main_flow():
    ingest_data()

# it doesn't seem this flow executes when you run it. Why?
# fix it ;^)

if __name__ == "__main__":
    main_flow()
