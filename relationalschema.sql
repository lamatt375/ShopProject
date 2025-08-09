Relational Schema

staff(id PK, name, email UNIQUE, role, created_at)

customers(id PK, first_name, last_name, email UNIQUE, created_at)

credit_cards(id PK, customer_id FK → customers.id, brand, last4, exp_month, exp_year, billing_zip, created_at)

products(id PK, name, description, category, price, stock_qty, created_at)

purchases(id PK, customer_id FK → customers.id, product_id FK → products.id, quantity, unit_price, total_amount, status, created_at)
