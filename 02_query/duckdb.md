# Working with DuckDB

Here are two sample CSV files we can browse/query using DuckDB:

    https://s3.amazonaws.com/uvasds-systems/data/customers-2M.csv
    https://s3.amazonaws.com/uvasds-systems/data/messy-10k.csv

## Reading a large remote CSV with the DuckDB CLI

DuckDB can query a CSV directly over HTTP without downloading it first. Launch the CLI:

    duckdb

Then create a view over the remote file so you can query it like a table:

```sql
CREATE VIEW customers AS
    SELECT * FROM read_csv_auto('https://s3.amazonaws.com/uvasds-systems/data/customers-2M.csv');

SELECT * FROM customers LIMIT 5;
```

## Browsing the schema

```sql
DESCRIBE customers;
```

```sql
SUMMARIZE customers;
```

`SUMMARIZE` gives per-column min, max, approximate distinct count, null %, and average — a fast way to profile every column at once.

## High/low values and other representations of key columns

Earliest and latest subscription dates:

```sql
SELECT MIN("Subscription Date") AS earliest, 
  MAX("Subscription Date") AS latest
FROM customers;
```

Top countries by customer count:

```sql
SELECT Country, COUNT(*) AS total
FROM customers
GROUP BY Country
ORDER BY total DESC
LIMIT 10;
```

Companies with the most listed customers:

```sql
SELECT Company, COUNT(*) AS total
FROM customers
GROUP BY Company
ORDER BY total DESC
LIMIT 10;
```

Subscriptions per year (distribution over time):

```sql
SELECT date_part('year', "Subscription Date") AS year, 
  COUNT(*) AS total
FROM customers
GROUP BY year
ORDER BY year;
```

Sanity check for nulls/blanks in an important column:

```sql
SELECT COUNT(*) FILTER (WHERE Email IS NULL OR Email = '') 
  AS missing_email
FROM customers;
```

## Saving the CSV as a local Parquet file

Once you've explored the data, write it to disk in Parquet format:

```sql
COPY (SELECT * FROM customers)
    TO 'customers-2M.parquet' (FORMAT PARQUET);
```

Confirm it worked by querying the new local file directly:

```sql
SELECT COUNT(*) FROM 'customers-2M.parquet';
```

Compare file sizes from the shell to see the compression difference:

    ls -lh customers-2M.csv customers-2M.parquet
