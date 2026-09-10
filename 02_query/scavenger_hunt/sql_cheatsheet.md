# SQL Cheat Sheet (DuckDB)

A quick reference for loading the case file and for each CRUD statement
you'll need. Examples below use a throwaway `pets` table — not the case
data — so copy the *pattern*, not the exact query.

---

## Loading the database

**Option A — build it from setup.sql in one shot (from your terminal):**
```bash
duckdb vanishing_dataset.db < setup.sql
```
This creates `vanishing_dataset.db` and runs every statement in
`setup.sql` against it. Do this once before you start.

**Option B — open the database, then load the script from inside DuckDB:**
```bash
duckdb vanishing_dataset.db
```
```sql
.read setup.sql
```

**Reopening a database you already built** (no need to re-run `setup.sql`
unless you want to start over):
```bash
duckdb vanishing_dataset.db
```

**Starting over from scratch** if you've made a mess:
```bash
duckdb vanishing_dataset.db < setup.sql
```
(`setup.sql` starts with `DROP TABLE IF EXISTS`, so this wipes and
rebuilds cleanly.)

**Useful DuckDB shell commands, once you're in:**
```sql
.tables              -- list all tables in the current database
.schema pets          -- show a table's column definitions
.quit                 -- exit the DuckDB shell
```

---

## CREATE — define a new table

```sql
CREATE TABLE pets (
    pet_id INTEGER PRIMARY KEY,
    name   VARCHAR(50),
    species VARCHAR(30),
    age    INTEGER
);
```
Every column needs a name and a type. `INTEGER`, `VARCHAR(n)` (text up
to `n` characters), and `DATE` cover almost everything you'll need here.

---

## INSERT — add a row

```sql
INSERT INTO pets VALUES (1, 'Biscuit', 'Dog', 4);
```
Values must be listed in the same order as the columns in `CREATE
TABLE`. You can also name the columns explicitly (safer if you're not
inserting every column, or don't want to rely on order):
```sql
INSERT INTO pets (pet_id, name, species, age) VALUES (2, 'Whiskers', 'Cat', 2);
```

---

## SELECT — read rows

Everything in a table:
```sql
SELECT * FROM pets;
```
Specific columns, filtered by a condition:
```sql
SELECT name, age FROM pets WHERE species = 'Dog';
```
Filtered by a range (works for numbers, dates, and text timestamps like
`'2026-09-09 23:05'`):
```sql
SELECT * FROM pets WHERE age BETWEEN 2 AND 5;
```
Sorted:
```sql
SELECT * FROM pets ORDER BY age DESC;
```
Joining two tables on a shared column:
```sql
SELECT p.name, o.owner_name
FROM pets p
JOIN owners o ON p.owner_id = o.owner_id;
```
Grouping + counting, with a filter on the *group* (`HAVING`, not `WHERE`):
```sql
SELECT species, COUNT(*) AS how_many
FROM pets
GROUP BY species
HAVING COUNT(*) > 1;
```
Pulling a substring out of a text column — `SUBSTR(column, start, length)`,
1-indexed:
```sql
SELECT SUBSTR(name, 1, 3) FROM pets;   -- first 3 characters of each name
```

---

## UPDATE — change existing rows

```sql
UPDATE pets SET age = 5 WHERE pet_id = 1;
```
**Always include a `WHERE` clause** — `UPDATE pets SET age = 5;` with no
`WHERE` changes *every row in the table*. If you're not sure your
`WHERE` is narrow enough, run the equivalent `SELECT` first to see
exactly which rows it would hit:
```sql
SELECT * FROM pets WHERE pet_id = 1;   -- check first...
UPDATE pets SET age = 5 WHERE pet_id = 1;  -- ...then update
```

---

## DELETE — remove rows

```sql
DELETE FROM pets WHERE pet_id = 2;
```
Same rule as `UPDATE`: **no `WHERE` clause means every row gets deleted.**
`DELETE FROM pets;` with nothing after it empties the whole table. Check
with `SELECT` first if you're unsure.

---

## Quick troubleshooting

- `Catalog Error: Table with name X does not exist` — you haven't run
  `setup.sql` yet, or you're pointed at the wrong `.db` file.
- Query returns 0 rows when you expected some — double check quotes
  around text/dates, and that you're matching the exact casing/spelling
  in the table.
- Made a mistake with `UPDATE`/`DELETE` and don't know how far it went —
  don't guess-fix it. Rebuild from `setup.sql` and start that step over.
