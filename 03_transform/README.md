# Transform Data using `dbt`

`dbt` (data build tool) is how data engineers turn raw, messy tables
into clean ones — using version-controlled SQL `SELECT` statements
instead of the manual `UPDATE`/`CREATE TABLE ... AS SELECT` cleanup
you did by hand in `02_query`. Each cleaning step becomes a named
**model** that dbt builds and rebuilds for you.

---

## 1. Install dbt

Pick whichever environment manager you're using — both install the
same DuckDB adapter (`dbt-duckdb`), which pulls in `dbt-core`
automatically.

**Option A: `pipenv`**

From the repo root:

```bash
pipenv install dbt-duckdb
pipenv shell
```

**Option B: `uv`**

From the repo root:

```bash
uv add dbt-duckdb
uv sync
```

Run dbt commands with `uv run dbt ...`, or activate the environment
first with `source .venv/bin/activate`.

Confirm it installed:

```bash
dbt --version
```

(or `uv run dbt --version` if you didn't activate the `uv` venv)

---

## 2. Initialize a dbt project

From this `03_transform/` folder:

```bash
dbt init ecommerce_dbt
```

When prompted, choose `duckdb` as the adapter. This creates an
`ecommerce_dbt/` folder with a `dbt_project.yml`, a `models/` folder,
and a starter `profiles.yml` (usually written to `~/.dbt/`).

---

## 3. Point dbt at the DuckDB database

Open `~/.dbt/profiles.yml` and point the `path` at the same database
file you've already been querying in `02_query/ecommerce/`:

```yaml
ecommerce_dbt:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: "../02_query/ecommerce/ecommerce.duckdb"
      threads: 4
```

Test the connection:

```bash
cd ecommerce_dbt
dbt debug
```

---

## 4. Write your first cleaning model

Create `models/stg_products.sql`. This is the same kind of cleanup
from `02_query`'s §7 — trimming/uppercasing `category`, dropping bad
rows — but now it's a reusable, version-controlled SQL file instead of
a one-off script:

```sql
-- models/stg_products.sql
select
    product_id,
    vendor_id,
    product_name,
    upper(trim(category)) as category,
    round(price, 2) as price,
    in_stock
from {{ source('ecommerce', 'products') }}
where price > 0
```

Declare the source table in `models/sources.yml`:

```yaml
version: 2

sources:
  - name: ecommerce
    schema: main
    tables:
      - name: products
```

Run it:

```bash
dbt run
```

dbt creates a new table (or view) named `stg_products` in the
database — your cleaned data, without ever overwriting the original
`products` table.

---

## 5. Why this matters for a pipeline

- **Idempotent**: re-running `dbt run` rebuilds the model the same way
  every time, instead of accumulating manual edits.
- **Traceable**: every transformation lives in SQL under version
  control, not in ad hoc shell history.
- **Testable**: `dbt test` can assert things like "no null
  `product_id`" or "`price` is never negative" before the cleaned data
  is trusted downstream.
- **Composable**: later models can `select from {{ ref('stg_products') }}`
  and build on top of already-cleaned data, one layer at a time.
