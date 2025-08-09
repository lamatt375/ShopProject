from tabulate import tabulate
from db import get_conn, query_products, add_product, update_stock, create_purchase, sales_report

def prompt(msg):
    return input(msg).strip()

def menu():
    print("\nMiniShop CLI")
    print("1) Search products")
    print("2) Create purchase")
    print("3) Sales report")
    print("4) Add product (staff)")
    print("5) Update stock (staff)")
    print("0) Exit")
    return prompt("Choose: ")

def do_search():
    kw = prompt("Keyword (blank for any): ")
    minp = prompt("Min price (blank for any): ")
    maxp = prompt("Max price (blank for any): ")
    minp = float(minp) if minp else None
    maxp = float(maxp) if maxp else None
    with get_conn() as conn:
        rows = query_products(conn, keyword=kw or None, min_price=minp, max_price=maxp)
    print(tabulate(rows, headers=["id", "name", "category", "price", "stock_qty"], tablefmt="github"))

def do_create_purchase():
    cid = prompt("Customer UUID: ")
    pid = prompt("Product UUID: ")
    qty = int(prompt("Quantity: "))
    try:
        with get_conn() as conn:
            purchase_id, total = create_purchase(conn, cid, pid, qty)
        print(f"Purchase {purchase_id} created. Total = ${total:.2f}")
    except Exception as e:
        print("Error:", e)

def do_sales_report():
    sd = prompt("Start date (YYYY-MM-DD, blank=any): ") or None
    ed = prompt("End date (YYYY-MM-DD, blank=any): ") or None
    mt = prompt("Min total (blank=any): ")
    mt = float(mt) if mt else None
    with get_conn() as conn:
        rows = sales_report(conn, sd, ed, mt)
    print(tabulate(rows, headers=["purchase_id", "created_at", "customer_email", "product_name", "quantity", "unit_price", "total_amount"], tablefmt="github"))

def do_add_product():
    name = prompt("Name: ")
    cat = prompt("Category: ")
    price = float(prompt("Price: "))
    stock = int(prompt("Stock qty: "))
    desc = prompt("Description (optional): ") or None
    with get_conn() as conn:
        pid = add_product(conn, name, cat, price, stock, desc)
    print(f"Added product {pid}")

def do_update_stock():
    pid = prompt("Product UUID: ")
    new_stock = int(prompt("New stock qty: "))
    with get_conn() as conn:
        update_stock(conn, pid, new_stock)
    print("Stock updated.")

if __name__ == "__main__":
    while True:
        choice = menu()
        if choice == "1":
            do_search()
        elif choice == "2":
            do_create_purchase()
        elif choice == "3":
            do_sales_report()
        elif choice == "4":
            do_add_product()
        elif choice == "5":
            do_update_stock()
        elif choice == "0":
            print("Bye!")
            break
        else:
            print("Invalid choice.")
