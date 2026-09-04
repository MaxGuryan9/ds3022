# Data / ENV Vars

## Key-Value Pairs (Environment Variables)

An environment variable is a **key-value pair** stored outside your program's code, in the shell or OS environment it runs in. Programs read these key-value pairs at runtime to pick up configuration (names, secrets, settings) without hardcoding them into the source. The **key** is the variable's name (e.g. `COURSE_NAME`), and the **value** is the string assigned to it (e.g. `"DS3022"`). This directory includes two small scripts that demonstrate setting, reading, and prompting for key-value pairs in Python and Bash.

    FNAME="Cassandra"  # sets an env variable in a shell/terminal.
    echo $FNAME        # prints out an existing env variable

## Scripts to Get/Put Env Vars

- **`env_vars.py`** — Python example that sets `COURSE_NAME` and `SEMESTER` as environment variables via `os.environ`, reads them back, and prompts the user for additional input (`input()`).
- **`env_vars.sh`** — Bash equivalent of the above: exports `COURSE_NAME` and `SEMESTER`, echoes them back, and prompts the user for input via `read`.

## Sample File Types

- **`FLIGHT_LOGS.csv`** — Sample dataset of 1,000 flight records (flight number, airline, departure/arrival airports and cities, times, duration, passenger details, ticket price, baggage weight, meal preference, flight status, gate number, arrival date).
- **`SIS.csv`** — Sample Student Information System dataset of 1,000 student records (student ID, name, age, email, major, enrollment/graduation dates, GPA, advisor, course load, campus location, housing status, student status, financial aid).
- **`INSTA.json`** — Sample Instagram-style dataset of 1,000 posts (post ID, username, caption, image URL, likes, comments, post date, hashtags, location, tagged users, engagement rate, video duration, story info, sponsored flag, post type, story type).

## Install DuckDB

Visit the [**DuckDB Installation**](https://duckdb.org/install/) page and install the CLI version to your laptop. In later exercises we will also use the DuckDB Python package.
