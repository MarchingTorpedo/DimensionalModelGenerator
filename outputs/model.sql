CREATE TABLE customers (
  customer_id INTEGER,
  first_name VARCHAR(50),
  last_name VARCHAR(50),
  email VARCHAR(50),
  signup_date VARCHAR(50),
  ,PRIMARY KEY (customer_id)
);

CREATE TABLE orders (
  order_id INTEGER,
  customer_id INTEGER,
  order_date VARCHAR(50),
  total FLOAT,
  ,PRIMARY KEY (order_id)
);

CREATE TABLE order_items (
  order_item_id INTEGER,
  order_id INTEGER,
  product_id INTEGER,
  quantity INTEGER,
  unit_price FLOAT,
  ,PRIMARY KEY (order_item_id)
);

CREATE TABLE products (
  product_id INTEGER,
  sku VARCHAR(50),
  name VARCHAR(50),
  category VARCHAR(50),
  price FLOAT,
  ,PRIMARY KEY (product_id)
);

CREATE TABLE product_catalog (
  product_id INTEGER,
  sku VARCHAR(50),
  attributes VARCHAR(50),
  ,PRIMARY KEY (product_id)
);

ALTER TABLE customers ADD FOREIGN KEY (customer_id) REFERENCES orders(customer_id);

ALTER TABLE orders ADD FOREIGN KEY (order_id) REFERENCES order_items(order_id);

ALTER TABLE orders ADD FOREIGN KEY (customer_id) REFERENCES customers(customer_id);

ALTER TABLE orders ADD FOREIGN KEY (total) REFERENCES order_items(unit_price);

ALTER TABLE orders ADD FOREIGN KEY (total) REFERENCES products(price);

ALTER TABLE order_items ADD FOREIGN KEY (order_id) REFERENCES orders(order_id);

ALTER TABLE order_items ADD FOREIGN KEY (product_id) REFERENCES products(product_id);

ALTER TABLE order_items ADD FOREIGN KEY (product_id) REFERENCES product_catalog(product_id);

ALTER TABLE order_items ADD FOREIGN KEY (quantity) REFERENCES customers(customer_id);

ALTER TABLE order_items ADD FOREIGN KEY (quantity) REFERENCES orders(customer_id);

ALTER TABLE order_items ADD FOREIGN KEY (unit_price) REFERENCES orders(total);

ALTER TABLE order_items ADD FOREIGN KEY (unit_price) REFERENCES products(price);

ALTER TABLE products ADD FOREIGN KEY (product_id) REFERENCES order_items(product_id);

ALTER TABLE products ADD FOREIGN KEY (product_id) REFERENCES product_catalog(product_id);

ALTER TABLE products ADD FOREIGN KEY (sku) REFERENCES product_catalog(sku);

ALTER TABLE products ADD FOREIGN KEY (price) REFERENCES orders(total);

ALTER TABLE products ADD FOREIGN KEY (price) REFERENCES order_items(unit_price);

ALTER TABLE product_catalog ADD FOREIGN KEY (product_id) REFERENCES order_items(product_id);

ALTER TABLE product_catalog ADD FOREIGN KEY (product_id) REFERENCES products(product_id);

ALTER TABLE product_catalog ADD FOREIGN KEY (sku) REFERENCES products(sku);