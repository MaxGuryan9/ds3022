-- ============================================================
-- Practice e-commerce database
-- ============================================================
-- A deliberately oversimplified e-commerce schema for practicing
-- CRUD (Create, Read, Update, Delete) operations in DuckDB.
--
-- Tables:
--   vendors    - companies that supply products
--   products   - items for sale, each tied to one vendor
--   customers  - people who place orders
--   orders     - one row per order, referencing a customer,
--                a product, and (via the product) a vendor
--
-- Foreign keys (customer_id, product_id, vendor_id in orders)
-- are NOT enforced with FOREIGN KEY constraints. This is
-- intentional -- we're assuming the INSERT data is already
-- correct, and keeping the DDL simple for teaching purposes.
-- ============================================================

-- Make the random values reproducible across runs
SELECT setseed(0.42);

-- ------------------------------------------------------------
-- 1. vendors
-- ------------------------------------------------------------
DROP TABLE IF EXISTS vendors;

CREATE TABLE vendors (
    vendor_id   INTEGER PRIMARY KEY,
    vendor_name VARCHAR NOT NULL,
    country     VARCHAR,
    rating      DECIMAL(2,1),
    active      BOOLEAN
);

INSERT INTO vendors
SELECT
    n AS vendor_id,
    list_value(
        'Blue Ridge Wholesale', 'Piedmont Import Co', 'Cascade Supply Group', 'Harbor & Vine Trading',
        'Summit Goods Collective', 'Ironclad Distribution', 'Sunrise Mercantile', 'Evergreen Trade Partners',
        'Pacific Rim Sourcing', 'Copperline Wholesale', 'Granite State Supply', 'Lonestar Distributors',
        'Meridian Trading Co', 'Northgate Wholesale', 'Redwood Import Partners', 'Silverline Goods',
        'Timberline Supply Co', 'Anchor Point Trading', 'Crestview Wholesale', 'Coastal Harbor Imports',
        'Union Square Suppliers', 'Brightline Distribution', 'Maple & Co Wholesale',
        'Foothill Trading Group', 'Vantage Point Supply'
    )[((n - 1) % 25) + 1] AS vendor_name,
    -- weighted toward the USA, like a real small-business vendor list would be
    list_value(
        'USA', 'USA', 'USA', 'USA', 'USA', 'USA',
        'Canada', 'Mexico', 'UK', 'Germany', 'China', 'Vietnam'
    )[((n * 5 - 3) % 12) + 1] AS country,
    round(3.2 + random() * 1.8, 1) AS rating,
    (random() > 0.1) AS active
FROM range(1, 26) AS t(n);

-- ------------------------------------------------------------
-- 2. products
-- ------------------------------------------------------------
DROP TABLE IF EXISTS products;

CREATE TABLE products (
    product_id   INTEGER PRIMARY KEY,
    vendor_id    INTEGER,               -- FK -> vendors.vendor_id (not enforced)
    product_name VARCHAR NOT NULL,
    category     VARCHAR,
    price        DECIMAL(10,2),
    in_stock     BOOLEAN
);

WITH gen AS (
    SELECT
        n AS product_id,
        ((n - 1) % 25) + 1 AS vendor_id,
        ((n - 1) % 8) + 1 AS category_idx,
        CAST((n - 1) / 8 AS INTEGER) % 13 + 1 AS item_idx,
        -- price range varies by category (electronics run higher than
        -- books, etc.), and every price ends in .99 like real retail
        -- listings do
        CAST(
            FLOOR(
                CASE ((n - 1) % 8) + 1
                    WHEN 1 THEN 12.99 + random() * 287   -- Electronics: $12.99-$299.99
                    WHEN 2 THEN 9.99  + random() * 120   -- Home & Kitchen: $9.99-$129.99
                    WHEN 3 THEN 9.99  + random() * 190   -- Sporting Goods: $9.99-$199.99
                    WHEN 4 THEN 3.99  + random() * 56    -- Office Supplies: $3.99-$59.99
                    WHEN 5 THEN 6.99  + random() * 43    -- Toys: $6.99-$49.99
                    WHEN 6 THEN 7.99  + random() * 22    -- Books: $7.99-$29.99
                    WHEN 7 THEN 9.99  + random() * 70    -- Apparel: $9.99-$79.99
                    WHEN 8 THEN 6.99  + random() * 143   -- Garden: $6.99-$149.99
                END
            ) + 0.99
        AS DECIMAL(10,2)) AS price,
        (random() > 0.15) AS in_stock
    FROM range(1, 101) AS t(n)
)
INSERT INTO products
SELECT
    product_id,
    vendor_id,
    CASE category_idx
        WHEN 1 THEN list_value(
            'Wireless Bluetooth Earbuds', '4K Streaming Media Player', 'Portable Bluetooth Speaker',
            'Noise Cancelling Headphones', 'USB-C Fast Charger', 'Smart LED Light Bulb',
            'Wireless Phone Charging Pad', 'HDMI Cable, 6ft', 'Mechanical Gaming Keyboard',
            'Wireless Optical Mouse', 'Portable Power Bank', 'Smart Home Security Camera',
            'Bluetooth Fitness Tracker'
        )[item_idx]
        WHEN 2 THEN list_value(
            'Stainless Steel Water Bottle', 'Non-Stick Frying Pan', 'Electric Kettle',
            'Ceramic Coffee Mug Set', 'Silicone Baking Mat', 'Knife Sharpener',
            'Bamboo Cutting Board', 'Digital Kitchen Scale', 'Air Fryer',
            'French Press Coffee Maker', 'Reusable Produce Bags', 'Glass Meal Prep Containers',
            'Electric Hand Mixer'
        )[item_idx]
        WHEN 3 THEN list_value(
            'Yoga Mat', 'Adjustable Dumbbell Set', 'Resistance Bands Set',
            'Foam Roller', 'Jump Rope', 'Hiking Backpack',
            'Insulated Water Bottle', 'Running Armband', 'Camping Tent',
            'Sleeping Bag', 'Bike Helmet', 'Golf Ball Set',
            'Tennis Racket'
        )[item_idx]
        WHEN 4 THEN list_value(
            'Mechanical Pencil Set', 'Sticky Notes Pack', 'Desk Organizer',
            'Wireless Presenter Remote', 'Ergonomic Chair Cushion', 'Heavy-Duty Stapler',
            'Whiteboard Markers Set', 'Cross-Cut Paper Shredder', 'Adjustable Laptop Stand',
            'Monitor Riser Stand', 'File Folder Set', 'Desk Lamp with USB Port',
            'Label Maker'
        )[item_idx]
        WHEN 5 THEN list_value(
            'Building Block Set', 'Remote Control Car', '1000-Piece Jigsaw Puzzle',
            'Plush Teddy Bear', 'Classic Board Game', 'Action Figure Set',
            'Art and Craft Kit', 'Wooden Train Set', 'Kids Tablet Case',
            'Bubble Machine', 'Water Balloon Set', 'Dinosaur Toy Set',
            'Play-Doh Variety Pack'
        )[item_idx]
        WHEN 6 THEN list_value(
            'Mystery Novel (Paperback)', 'Bestselling Cookbook', 'Children''s Picture Book',
            'Self-Help Guide', 'Historical Fiction Novel', 'Science Fiction Epic',
            'Graphic Novel Collection', 'Journal and Notebook Set', 'Poetry Anthology',
            'Travel Guide Book', 'Bestselling Biography', 'Fantasy Novel Series',
            'Puzzle and Activity Book'
        )[item_idx]
        WHEN 7 THEN list_value(
            'Cotton Crew Neck T-Shirt', 'Fleece Zip-Up Hoodie', 'Slim Fit Jeans',
            'Running Shorts', 'Wool Blend Socks (3-Pack)', 'Baseball Cap',
            'Packable Rain Jacket', 'Winter Puffer Vest', 'Yoga Leggings',
            'Flannel Button-Down Shirt', 'Canvas Sneakers', 'Thermal Base Layer Set',
            'Knit Beanie'
        )[item_idx]
        WHEN 8 THEN list_value(
            'Garden Hose, 50ft', 'Pruning Shears', 'Solar Pathway Lights (Set of 8)',
            'Raised Garden Bed Kit', 'Potting Soil Mix', 'Galvanized Watering Can',
            'Hanging Bird Feeder', 'Garden Gloves', 'Outdoor Planter Pot',
            'Grass Seed Bag', 'Leaf Rake', 'Patio Furniture Cover',
            'Wind Chime'
        )[item_idx]
    END AS product_name,
    list_value(
        'Electronics', 'Home & Kitchen', 'Sporting Goods', 'Office Supplies',
        'Toys', 'Books', 'Apparel', 'Garden'
    )[category_idx] AS category,
    price,
    in_stock
FROM gen;

-- ------------------------------------------------------------
-- 3. customers
-- ------------------------------------------------------------
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    first_name  VARCHAR NOT NULL,
    last_name   VARCHAR NOT NULL,
    email       VARCHAR,
    city        VARCHAR,
    state       VARCHAR,
    signup_date DATE
);

WITH names AS (
    SELECT
        n AS customer_id,
        list_value(
            'James', 'Mary', 'Robert', 'Patricia', 'John', 'Jennifer', 'Michael', 'Linda',
            'David', 'Elizabeth', 'William', 'Barbara', 'Richard', 'Susan', 'Joseph',
            'Jessica', 'Thomas', 'Sarah', 'Charles', 'Karen', 'Daniel', 'Nancy',
            'Matthew', 'Lisa', 'Anthony', 'Betty', 'Mark', 'Margaret', 'Steven', 'Sandra'
        )[((n - 1) % 30) + 1] AS first_name,
        -- 29 is coprime with 30, so this cycles through last names on a
        -- different rhythm than first names, avoiding repeated pairings
        list_value(
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller',
            'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson',
            'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee',
            'Perez', 'Thompson', 'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis'
        )[((n * 7 - 2) % 29) + 1] AS last_name,
        -- 20 real city/state pairs, indexed together so city and state
        -- always match (unlike picking each independently)
        list_value(
            'New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix',
            'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'Austin',
            'Charlotte', 'Columbus', 'Indianapolis', 'Seattle', 'Denver',
            'Boston', 'Nashville', 'Portland', 'Charlottesville', 'Richmond'
        )[((n - 1) % 20) + 1] AS city,
        list_value(
            'NY', 'CA', 'IL', 'TX', 'AZ',
            'PA', 'TX', 'CA', 'TX', 'TX',
            'NC', 'OH', 'IN', 'WA', 'CO',
            'MA', 'TN', 'OR', 'VA', 'VA'
        )[((n - 1) % 20) + 1] AS state,
        list_value(
            'gmail.com', 'yahoo.com', 'outlook.com', 'icloud.com', 'hotmail.com'
        )[((n * 2 - 1) % 5) + 1] AS email_domain,
        -- most customers signed up sometime in the last ~4 years
        CURRENT_DATE - CAST(random() * 1460 AS INTEGER) AS signup_date
    FROM range(1, 101) AS t(n)
)
INSERT INTO customers
SELECT
    customer_id,
    first_name,
    last_name,
    -- realistic-looking address: firstname.lastname@domain, with a
    -- number tacked on for ~35% of rows (as real accounts often need,
    -- since "john.smith" alone gets taken fast)
    lower(first_name) || '.' || lower(last_name)
        || CASE WHEN random() < 0.35 THEN CAST(1 + CAST(random() * 98 AS INTEGER) AS VARCHAR) ELSE '' END
        || '@' || email_domain AS email,
    city,
    state,
    signup_date
FROM names;

-- ------------------------------------------------------------
-- 4. orders
-- ------------------------------------------------------------
-- Note: product_id and customer_id are picked pseudo-randomly.
-- vendor_id is pulled from the matching product so the data is
-- internally consistent (an order's vendor really did make the
-- ordered product), even though nothing enforces this in DDL.
--
-- order_date is derived from the customer's signup_date, so no
-- order can happen before the customer's account existed -- a
-- small touch that makes the data hang together logically.
-- ------------------------------------------------------------
DROP TABLE IF EXISTS orders;

CREATE TABLE orders (
    order_id    INTEGER PRIMARY KEY,
    customer_id INTEGER,   -- FK -> customers.customer_id (not enforced)
    product_id  INTEGER,   -- FK -> products.product_id  (not enforced)
    vendor_id   INTEGER,   -- FK -> vendors.vendor_id    (not enforced)
    quantity    INTEGER,
    order_date  DATE,
    status      VARCHAR
);

WITH order_base AS (
    SELECT
        n AS order_id,
        1 + CAST(random() * 99 AS INTEGER) AS customer_id,
        1 + CAST(random() * 99 AS INTEGER) AS product_id,
        -- most orders are for 1-2 items; a handful are bulkier
        CASE
            WHEN random() < 0.50 THEN 1
            WHEN random() < 0.75 THEN 2
            WHEN random() < 0.90 THEN 3
            WHEN random() < 0.97 THEN 4
            ELSE 5
        END AS quantity,
        -- most orders have already resolved one way or another;
        -- fewer are still pending or got cancelled
        CASE
            WHEN random() < 0.45 THEN 'delivered'
            WHEN random() < 0.70 THEN 'shipped'
            WHEN random() < 0.85 THEN 'pending'
            ELSE 'cancelled'
        END AS status
    FROM range(1, 101) AS t(n)
)
INSERT INTO orders
SELECT
    ob.order_id,
    ob.customer_id,
    ob.product_id,
    p.vendor_id,
    ob.quantity,
    c.signup_date + CAST(
        random() * GREATEST(DATE_DIFF('day', c.signup_date, CURRENT_DATE), 1) AS INTEGER
    ) AS order_date,
    ob.status
FROM order_base ob
JOIN products p ON p.product_id = ob.product_id
JOIN customers c ON c.customer_id = ob.customer_id;
