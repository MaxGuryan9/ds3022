# Practice: CRUD with a mini e-commerce database

> Shared In-Class SQL Queries: https://pad.riseup.net/p/CYj9RDBVhvGablNmraZH-keep

This folder has one file, `ecommerce_practice.sql`, that builds a tiny,
oversimplified e-commerce database in DuckDB:

| Table       | Rows | Description                                                        |
|-------------|------|----------------------------------------------------------------------|
| `vendors`   | 25   | Companies that supply products                                       |
| `products`  | 100  | Items for sale (Amazon-style names/categories), each made by one vendor |
| `customers` | 100  | People who place orders                                               |
| `orders`    | 100  | One row per order                                                     |

`orders` references `customers`, `products`, and `vendors` by their
primary keys (`customer_id`, `product_id`, `vendor_id`), but there are
no `FOREIGN KEY` constraints in the DDL — we're just trusting that the
`INSERT` data lines up correctly. This keeps the schema simple while
still letting you practice real joins.

Use this folder to practice the four CRUD operations: **C**reate,
**R**ead, **U**pdate, **D**elete.

The dummy data is generated (not hand-typed) but aims to feel real:
realistic US city/state pairs, `firstname.lastname@gmail.com`-style
emails, prices that vary by category and end in `.99` like real retail
listings, and order dates that are always on or after the ordering
customer's signup date. Every run of the script produces the same data
(via `setseed`), so your results will match the examples below.

---

## 1. Load the SQL file into a local DuckDB database

From this `practice/` folder, run:

```bash
duckdb ecommerce.duckdb < ecommerce_practice.sql
```

This creates a new file, `ecommerce.duckdb`, in the current directory
(or reuses it if it already exists) and runs the script against it.
The script starts with `DROP TABLE IF EXISTS ...` for each table, so
it's safe to re-run any time you want to reset back to the original
dummy data.

To work inside the database interactively instead of piping a file in,
open it directly:

```bash
duckdb ecommerce.duckdb
```

That drops you into the DuckDB shell, connected to `ecommerce.duckdb`.
From here on, the examples assume you're inside that shell. (Every
DuckDB shell command below ends in a semicolon — don't forget it, or
the shell will just wait for more input.)

---

## 2. Inspect the tables (Read)

List the tables in the database:

```sql
SHOW TABLES;
```

Look at a table's structure:

```sql
DESCRIBE products;
```

Peek at some rows:

```sql
SELECT * FROM vendors LIMIT 5;
SELECT * FROM products LIMIT 5;
SELECT * FROM customers LIMIT 5;
SELECT * FROM orders LIMIT 5;
```

Basic counts and filters:

```sql
-- How many products does each vendor sell?
SELECT vendor_id, count(*) AS num_products
FROM products
GROUP BY vendor_id
ORDER BY num_products DESC;

-- Orders that are still pending
SELECT * FROM orders WHERE status = 'pending';
```

Show unique values for a specific column:

```sql
SELECT DISTINCT category FROM products;
SELECT DISTINCT status FROM orders;
SELECT DISTINCT state FROM customers;
```

---

## 3. Insert a new record (Create)

Add a new vendor:

```sql
INSERT INTO vendors (vendor_id, vendor_name, country, rating, active)
VALUES (16, 'Practice Vendor Co', 'USA', 4.5, true);
```

Add a product from that vendor:

```sql
INSERT INTO products (product_id, vendor_id, product_name, category, price, in_stock)
VALUES (101, 16, 'Practice Widget', 'Electronics', 24.99, true);
```

Add a new customer:

```sql
INSERT INTO customers (customer_id, first_name, last_name, email, city, state, signup_date)
VALUES (101, 'Pat', 'Newcomer', 'pat.newcomer@example.com', 'Charlottesville', 'VA', current_date);
```

Now place an order for that customer and product:

```sql
INSERT INTO orders (order_id, customer_id, product_id, vendor_id, quantity, order_date, status)
VALUES (101, 101, 101, 16, 1, current_date, 'pending');
```

Notice that `vendor_id` in the `orders` row (16) matches the
`vendor_id` on the `products` row for `product_id = 101`. Nothing in
the schema forces that to be true — it's on you (or your application
code) to keep it consistent.

Verify it landed:

```sql
SELECT * FROM orders WHERE order_id = 101;
```

---

## 4. Update an existing record

Say the practice order shipped. Update its status:

```sql
UPDATE orders
SET status = 'shipped'
WHERE order_id = 101;
```

Give the practice vendor a better rating:

```sql
UPDATE vendors
SET rating = 4.8
WHERE vendor_id = 16;
```

Always include a `WHERE` clause on an `UPDATE` — without one, DuckDB
will happily update *every row* in the table. Check your change:

```sql
SELECT * FROM orders WHERE order_id = 101;
```

---

## 5. Delete a record

Delete the practice order:

```sql
DELETE FROM orders WHERE order_id = 101;
```

As with `UPDATE`, always scope `DELETE` with a `WHERE` clause. Confirm
it's gone:

```sql
SELECT * FROM orders WHERE order_id = 101;
-- should return 0 rows
```

(Leave the vendor, product, and customer rows in place for now — the
next section reuses `customer_id = 3` and other original rows to build
a full order view.)

---

## 6. Build up to a full order view (joins)

The real payoff of a relational schema is being able to reassemble a
full picture of one order by joining across all four tables. Build
this up one join at a time.

**Start with just the order and its customer:**

```sql
SELECT
    o.order_id,
    o.order_date,
    o.status,
    c.first_name,
    c.last_name,
    c.email
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
WHERE o.order_id = 3;
```

**Add the product being ordered:**

```sql
SELECT
    o.order_id,
    o.order_date,
    o.status,
    c.first_name,
    c.last_name,
    p.product_name,
    p.category,
    p.price,
    o.quantity
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
JOIN products  p ON p.product_id  = o.product_id
WHERE o.order_id = 3;
```

**Add the vendor that made the product:**

```sql
SELECT
    o.order_id,
    o.order_date,
    o.status,
    c.first_name,
    c.last_name,
    p.product_name,
    p.category,
    p.price,
    o.quantity,
    (p.price * o.quantity) AS line_total,
    v.vendor_name,
    v.country AS vendor_country
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
JOIN products  p ON p.product_id  = o.product_id
JOIN vendors   v ON v.vendor_id   = o.vendor_id
WHERE o.order_id = 3;
```

That final query is the "full view" of a single order: who bought
what, from which vendor, for how much, and what the order's status is
— pulled together from four separate tables with three joins.

Try changing `WHERE o.order_id = 3` to a few other order IDs (1–100),
or drop the `WHERE` clause entirely (maybe add a `LIMIT 10`) to see the
full picture across many orders at once.

---

## 7. Data Cleaning

Real-world tables are rarely as clean as this dummy data. A data
engineer often needs to fix bad values, drop rows that shouldn't be
there, or reshape a column — and do it safely, without risking the
original table if something goes wrong.

**Delete rows that don't belong.** Say some `products` rows snuck in
with a bogus price of `0` (a common sign of a bad import):

```sql
DELETE FROM products WHERE price <= 0;
```

**Transform an entire column based on a condition.** Say every
`customers` row from `'CA'` should actually read `'California'`
(mixing abbreviations and full names is a classic data-quality bug):

```sql
UPDATE customers
SET state = 'California'
WHERE state = 'CA';
```

Or normalize a whole column at once — trim stray whitespace and force
consistent casing on every category name:

```sql
UPDATE products
SET category = UPPER(TRIM(category));
```

**The safer pattern: `SELECT ... INTO` a new table first.** Rather
than transforming a table in place, engineers often build the cleaned
version into a brand-new table, check it, and only then swap it in.
That way the original data still exists if the transformation was
wrong.

Build a cleaned copy of `products` (rounding every price to two
decimal places and dropping anything with a null category) into a new
table:

```sql
CREATE TABLE products_clean AS
SELECT
    product_id,
    vendor_id,
    product_name,
    category,
    ROUND(price, 2) AS price,
    in_stock
FROM products
WHERE category IS NOT NULL;
```

Compare the two tables before committing to the change:

```sql
SELECT count(*) FROM products;
SELECT count(*) FROM products_clean;
```

Once you're satisfied `products_clean` looks right, drop the original
and rename the clean table to take its place:

```sql
DROP TABLE products;
ALTER TABLE products_clean RENAME TO products;
```

`products` is now the cleaned table, and you never ran a destructive
`UPDATE`/`DELETE` directly against the original data until you'd
already verified the replacement.

---

## 8. Practice on your own

A few ideas to try, using what you just learned:

1. **Create** a second new vendor, product, customer, and order —
   same as above, but pick your own IDs and make sure the `vendor_id`
   on your order matches the `vendor_id` on your product.
2. **Read**: write a query that joins `orders`, `products`, and
   `vendors` to find the total revenue (`price * quantity`) per
   vendor.
3. **Update**: mark every order older than `2024-06-01` with a status
   of `'delivered'` and a status of `'pending'` as `'cancelled'`
   instead — think about what `WHERE` conditions you'd need to do this
   safely in two separate statements.
4. **Delete**: remove a product that has no orders referencing it (use
   a `NOT IN` or `NOT EXISTS` subquery against `orders` to find one
   first).
5. Reset everything back to the original dummy data by re-running:

   ```bash
   duckdb ecommerce.duckdb < ecommerce_practice.sql
   ```
