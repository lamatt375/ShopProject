import os
from contextlib import contextmanager
from dotenv import load_dotenv
import psycopg

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Put it in .env or your shell environment.")

@contextmanager
def get_conn():
    with psycopg.connect(DATABASE_URL, autocommit=False) as conn:
        yield conn

def query_products(conn, keyword=None, min_price=None, max_price=None):
    base_sql = """
    SELECT id, name, category, price, stock_qty
    FROM public.products
    WHERE TRUE
    """
    conds = []
    params = {}

    if keyword and keyword.strip():
        conds.append("name ILIKE %(kw_like)s")
        params["kw_like"] = f"%{keyword.strip()}%"

    if min_price is not None:
        conds.append("price >= %(minp)s::numeric")
        params["minp"] = min_price

    if max_price is not None:
        conds.append("price <= %(maxp)s::numeric")
        params["maxp"] = max_price

    if conds:
        base_sql += " AND " + " AND ".join(conds)

    base_sql += " ORDER BY name LIMIT 100;"
    with conn.cursor() as cur:
        cur.execute(base_sql, params)
        return cur.fetchall()

def add_product(conn, name, category, price, stock_qty, description=None):
    sql = """
    INSERT INTO public.products (name, description, category, price, stock_qty)
    VALUES (%s, %s, %s, %s, %s)
    RETURNING id;
    """
    with conn.cursor() as cur:
        cur.execute(sql, (name, description, category, price, stock_qty))
        new_id = cur.fetchone()[0]
    conn.commit()
    return new_id

def update_stock(conn, product_id, new_stock):
    sql = "UPDATE public.products SET stock_qty = %s WHERE id = %s;"
    with conn.cursor() as cur:
        cur.execute(sql, (new_stock, product_id))
    conn.commit()

def create_purchase(conn, customer_id, product_id, quantity):
    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT price, stock_qty
                FROM public.products
                WHERE id = %(pid)s
                FOR UPDATE
            """, {"pid": product_id})
            row = cur.fetchone()
            if not row:
                raise ValueError("Product not found.")
            unit_price, stock_qty = row
            if quantity > stock_qty:
                raise ValueError(f"Insufficient stock: have {stock_qty}, need {quantity}.")

            total = round(unit_price * quantity, 2)

            cur.execute("""
                INSERT INTO public.purchases
                    (customer_id, product_id, quantity, unit_price, total_amount, status)
                VALUES
                    (%(cid)s, %(pid)s, %(qty)s, %(price)s, %(total)s, 'PAID')
                RETURNING id
            """, {"cid": customer_id, "pid": product_id, "qty": quantity,
                  "price": unit_price, "total": total})
            (purchase_id,) = cur.fetchone()

            cur.execute("""
                UPDATE public.products
                SET stock_qty = stock_qty - %(qty)s
                WHERE id = %(pid)s
            """, {"qty": quantity, "pid": product_id})

            return purchase_id, total

def sales_report(conn, start_date=None, end_date=None, min_total=None):
    base = """
        SELECT
          p.id            AS purchase_id,
          p.created_at,
          c.email         AS customer_email,
          pr.name         AS product_name,
          p.quantity,
          p.unit_price,
          p.total_amount
        FROM public.purchases p
        JOIN public.customers c ON c.id = p.customer_id
        JOIN public.products  pr ON pr.id = p.product_id
        WHERE TRUE
    """
    conds = []
    params = {}

    if start_date:
        conds.append("p.created_at >= %(sd)s::timestamptz")
        params["sd"] = start_date

    if end_date:
        conds.append("p.created_at < (%(ed)s::date + interval '1 day')")
        params["ed"] = end_date

    if min_total is not None:
        conds.append("p.total_amount >= %(mt)s::numeric")
        params["mt"] = min_total

    if conds:
        base += " AND " + " AND ".join(conds)

    base += " ORDER BY p.created_at DESC"

    with conn.cursor() as cur:
        cur.execute(base, params)
        return cur.fetchall()
