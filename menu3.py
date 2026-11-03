"""
Restaurant POS & Inventory Manager
----------------------------------
A desktop restaurant order-taking application built with Python's Tkinter and SQLite.

Run:
    python restaurant_pos.py

No third-party packages are required. The SQLite database (restaurant_pos.db) is
created automatically in the same folder as this script.
"""

import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, date
from pathlib import Path

DB_PATH = Path(__file__).with_name("restaurant_pos.db")

# ----------------------------- Database layer -----------------------------

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.setup()

    def setup(self):
        cur = self.conn.cursor()
        cur.executescript("""
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS dishes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                category TEXT NOT NULL,
                price REAL NOT NULL CHECK(price >= 0),
                stock INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0),
                active INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                total REAL NOT NULL,
                payment_method TEXT NOT NULL DEFAULT 'Cash'
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL REFERENCES orders(id),
                dish_id INTEGER,
                dish_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL
            );
        """)
        count = cur.execute("SELECT COUNT(*) FROM dishes").fetchone()[0]
        if count == 0:
            samples = [
                ("Chicken Biriyani", "Main Course", 160, 25),
                ("Veg Biriyani", "Main Course", 120, 20),
                ("Porotta", "Breads", 15, 80),
                ("Chapati", "Breads", 12, 60),
                ("Chicken Fried Rice", "Chinese", 150, 18),
                ("Veg Fried Rice", "Chinese", 120, 18),
                ("Gobi Manchurian", "Starters", 110, 15),
                ("Chicken 65", "Starters", 140, 12),
                ("Fresh Lime", "Drinks", 35, 40),
                ("Tea", "Drinks", 15, 60),
                ("Falooda", "Desserts", 90, 10),
            ]
            cur.executemany(
                "INSERT INTO dishes(name,category,price,stock) VALUES(?,?,?,?)",
                samples
            )
        self.conn.commit()

    def dishes(self, category=None, include_inactive=False):
        sql = "SELECT * FROM dishes"
        args = []
        conditions = []
        if not include_inactive:
            conditions.append("active=1")
        if category and category != "All":
            conditions.append("category=?")
            args.append(category)
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        return self.conn.execute(sql + " ORDER BY category, name", args).fetchall()

    def categories(self):
        rows = self.conn.execute(
            "SELECT DISTINCT category FROM dishes WHERE active=1 ORDER BY category"
        ).fetchall()
        return ["All"] + [r[0] for r in rows]

    def add_dish(self, name, category, price, stock):
        self.conn.execute(
            "INSERT INTO dishes(name,category,price,stock) VALUES(?,?,?,?)",
            (name, category, price, stock)
        )
        self.conn.commit()

    def update_stock(self, dish_id, amount):
        self.conn.execute(
            "UPDATE dishes SET stock=stock+? WHERE id=?",
            (amount, dish_id)
        )
        self.conn.commit()

    def update_dish(self, dish_id, name, category, price, stock):
        self.conn.execute(
            "UPDATE dishes SET name=?, category=?, price=?, stock=? WHERE id=?",
            (name, category, price, stock, dish_id)
        )
        self.conn.commit()

    def delete_dish(self, dish_id):
        self.conn.execute("UPDATE dishes SET active=0 WHERE id=?", (dish_id,))
        self.conn.commit()

    def checkout(self, cart, payment):
        # Validate stock again at checkout, then save order and reduce inventory.
        for dish_id, item in cart.items():
            row = self.conn.execute(
                "SELECT stock FROM dishes WHERE id=? AND active=1", (dish_id,)
            ).fetchone()
            if row is None or row["stock"] < item["qty"]:
                raise ValueError(f"Not enough stock for {item['name']}.")
        total = sum(x["qty"] * x["price"] for x in cart.values())
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO orders(created_at,total,payment_method) VALUES(?,?,?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), total, payment)
        )
        order_id = cur.lastrowid
        for dish_id, item in cart.items():
            cur.execute(
                """INSERT INTO order_items(order_id,dish_id,dish_name,quantity,unit_price)
                   VALUES(?,?,?,?,?)""",
                (order_id, dish_id, item["name"], item["qty"], item["price"])
            )
            cur.execute(
                "UPDATE dishes SET stock=stock-? WHERE id=?",
                (item["qty"], dish_id)
            )
        self.conn.commit()
        return order_id, total

    def sales_summary(self):
        today = date.today().isoformat()
        today_row = self.conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(total),0) FROM orders WHERE date(created_at)=?",
            (today,)
        ).fetchone()
        all_row = self.conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(total),0) FROM orders"
        ).fetchone()
        low = self.conn.execute(
            "SELECT COUNT(*) FROM dishes WHERE active=1 AND stock<=5"
        ).fetchone()[0]
        return {
            "today_orders": today_row[0],
            "today_sales": today_row[1],
            "all_orders": all_row[0],
            "all_sales": all_row[1],
            "low_stock": low,
        }

    def recent_orders(self, limit=12):
        return self.conn.execute(
            "SELECT * FROM orders ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()

    def order_items(self, order_id):
        return self.conn.execute(
            "SELECT * FROM order_items WHERE order_id=? ORDER BY id", (order_id,)
        ).fetchall()

    def close(self):
        self.conn.close()


# ------------------------------- UI helpers -------------------------------

BG = "#F4F6FA"
PANEL = "#FFFFFF"
NAVY = "#17243A"
NAVY2 = "#223652"
ACCENT = "#2878E5"
ACCENT_LIGHT = "#EAF2FF"
TEXT = "#1E293B"
MUTED = "#718096"
GREEN = "#15966A"
RED = "#D94B4B"
BORDER = "#E4E9F1"

FONT = ("Helvetica", 10)
FONT_BOLD = ("Helvetica", 10, "bold")
FONT_SMALL = ("Helvetica", 9)
FONT_TITLE = ("Helvetica", 22, "bold")


def money(value):
    return f"₹{value:,.2f}"


class RestaurantPOS(tk.Tk):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.title("ServePoint | Restaurant POS")
        self.geometry("1280x790")
        self.minsize(1040, 650)
        self.configure(bg=BG)
        self.cart = {}
        self.current_category = "All"
        self.current_page = "Dashboard"
        self._setup_style()
        self._build_shell()
        self.show_page("Dashboard")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _setup_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", background="white", fieldbackground="white",
                        foreground=TEXT, rowheight=32, font=FONT)
        style.configure("Treeview.Heading", background="#EEF2F7",
                        foreground=NAVY, font=FONT_BOLD, relief="flat")
        style.map("Treeview", background=[("selected", ACCENT_LIGHT)],
                  foreground=[("selected", NAVY)])
        style.configure("TCombobox", padding=6)
        style.configure("TEntry", padding=7)

    def _build_shell(self):
        self.sidebar = tk.Frame(self, bg=NAVY, width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        brand = tk.Frame(self.sidebar, bg=NAVY)
        brand.pack(fill="x", padx=20, pady=(25, 28))
        tk.Label(brand, text="●", fg="#65A6FF", bg=NAVY,
                 font=("Helvetica", 19, "bold")).pack(side="left")
        tk.Label(brand, text="  ServePoint", fg="white", bg=NAVY,
                 font=("Helvetica", 17, "bold")).pack(side="left")
        tk.Label(self.sidebar, text="RESTAURANT MANAGEMENT", bg=NAVY,
                 fg="#8FA2BC", font=("Helvetica", 8, "bold")).pack(
                     anchor="w", padx=20, pady=(0, 12))

        self.nav_buttons = {}
        for label, icon in [
            ("Dashboard", "▦"), ("New Order", "＋"), ("Menu & Dishes", "☷"),
            ("Inventory", "▤"), ("Sales History", "▥")
        ]:
            btn = tk.Button(
                self.sidebar, text=f"  {icon}   {label}", anchor="w",
                bg=NAVY, fg="#D8E2EF", activebackground=NAVY2,
                activeforeground="white", relief="flat", bd=0,
                font=("Helvetica", 11), padx=18, pady=13,
                command=lambda page=label: self.show_page(page), cursor="hand2"
            )
            btn.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[label] = btn

        tk.Frame(self.sidebar, bg="#34445C", height=1).pack(
            fill="x", padx=18, pady=(25, 14))
        tk.Label(self.sidebar, text="LOCAL DATABASE", bg=NAVY,
                 fg="#8FA2BC", font=("Helvetica", 8, "bold")).pack(
                     anchor="w", padx=20)
        tk.Label(self.sidebar, text="Your data is saved on this computer.",
                 bg=NAVY, fg="#AAB8CA", font=FONT_SMALL,
                 wraplength=175, justify="left").pack(
                     anchor="w", padx=20, pady=(7, 0))

        self.main = tk.Frame(self, bg=BG)
        self.main.pack(side="left", fill="both", expand=True)
        self.header = tk.Frame(self.main, bg=PANEL, height=72,
                               highlightbackground=BORDER, highlightthickness=1)
        self.header.pack(fill="x")
        self.header.pack_propagate(False)
        self.page_title = tk.Label(self.header, text="", bg=PANEL,
                                   fg=NAVY, font=("Helvetica", 17, "bold"))
        self.page_title.pack(side="left", padx=28)
        self.header_right = tk.Label(self.header, text="", bg=PANEL,
                                     fg=MUTED, font=FONT)
        self.header_right.pack(side="right", padx=28)
        self.content = tk.Frame(self.main, bg=BG)
        self.content.pack(fill="both", expand=True, padx=25, pady=22)

    def show_page(self, page):
        self.current_page = page
        for name, btn in self.nav_buttons.items():
            btn.configure(bg=NAVY2 if name == page else NAVY,
                          fg="white" if name == page else "#D8E2EF")
        for child in self.content.winfo_children():
            child.destroy()
        self.page_title.configure(text=page)
        self.header_right.configure(
            text=datetime.now().strftime("%a, %d %b %Y  •  %I:%M %p")
        )
        if page == "Dashboard":
            self.page_dashboard()
        elif page == "New Order":
            self.page_order()
        elif page == "Menu & Dishes":
            self.page_menu()
        elif page == "Inventory":
            self.page_inventory()
        elif page == "Sales History":
            self.page_sales()

    def card(self, parent, title, value, subtitle, color=ACCENT):
        frame = tk.Frame(parent, bg=PANEL, highlightbackground=BORDER,
                         highlightthickness=1)
        tk.Label(frame, text=title.upper(), bg=PANEL, fg=MUTED,
                 font=("Helvetica", 8, "bold")).pack(anchor="w", padx=17, pady=(15, 5))
        tk.Label(frame, text=value, bg=PANEL, fg=color,
                 font=("Helvetica", 23, "bold")).pack(anchor="w", padx=17)
        tk.Label(frame, text=subtitle, bg=PANEL, fg=MUTED,
                 font=FONT_SMALL).pack(anchor="w", padx=17, pady=(4, 15))
        return frame

    def section_title(self, parent, title, subtitle=None):
        tk.Label(parent, text=title, bg=BG, fg=NAVY,
                 font=("Helvetica", 13, "bold")).pack(anchor="w")
        if subtitle:
            tk.Label(parent, text=subtitle, bg=BG, fg=MUTED,
                     font=FONT_SMALL).pack(anchor="w", pady=(3, 10))

    def make_tree(self, parent, columns, headings, widths=None, height=10):
        wrap = tk.Frame(parent, bg=PANEL, highlightbackground=BORDER,
                        highlightthickness=1)
        tree = ttk.Treeview(wrap, columns=columns, show="headings", height=height)
        for i, col in enumerate(columns):
            tree.heading(col, text=headings[i])
            tree.column(col, width=(widths[i] if widths else 120),
                        anchor="w" if i == 0 else "center")
        yscroll = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=yscroll.set)
        tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        yscroll.pack(side="right", fill="y", padx=(0, 5), pady=8)
        return wrap, tree

    # ------------------------------- Dashboard -------------------------------

    def page_dashboard(self):
        stats = self.db.sales_summary()
        cards = tk.Frame(self.content, bg=BG)
        cards.pack(fill="x", pady=(0, 22))
        data = [
            ("Today's Revenue", money(stats["today_sales"]), "Sales recorded today", ACCENT),
            ("Orders Today", str(stats["today_orders"]), "Completed orders", GREEN),
            ("Total Revenue", money(stats["all_sales"]), "All-time sales", "#805AD5"),
            ("Low Stock Items", str(stats["low_stock"]), "5 units or less", RED),
        ]
        for title, value, sub, color in data:
            c = self.card(cards, title, value, sub, color)
            c.pack(side="left", fill="both", expand=True, padx=(0, 12))

        lower = tk.Frame(self.content, bg=BG)
        lower.pack(fill="both", expand=True)
        left = tk.Frame(lower, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 14))
        self.section_title(left, "Recent orders", "Latest completed transactions")
        wrap, tree = self.make_tree(
            left, ("id", "date", "payment", "total"),
            ("Order ID", "Date & Time", "Payment", "Total"),
            (90, 220, 110, 120), 11
        )
        wrap.pack(fill="both", expand=True)
        for row in self.db.recent_orders(15):
            tree.insert("", "end", values=(
                f"#{row['id']}", row["created_at"], row["payment_method"],
                money(row["total"])
            ))

        right = tk.Frame(lower, bg=PANEL, width=250,
                         highlightbackground=BORDER, highlightthickness=1)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)
        tk.Label(right, text="Quick actions", bg=PANEL, fg=NAVY,
                 font=("Helvetica", 13, "bold")).pack(anchor="w", padx=18, pady=(18, 15))
        self.action_button(right, "＋  Create new order",
                           lambda: self.show_page("New Order")).pack(fill="x", padx=15, pady=5)
        self.action_button(right, "＋  Add a dish",
                           lambda: self.open_dish_dialog()).pack(fill="x", padx=15, pady=5)
        self.action_button(right, "▤  Update stock",
                           lambda: self.show_page("Inventory")).pack(fill="x", padx=15, pady=5)
        tk.Label(right, text="Tip", bg=PANEL, fg=ACCENT,
                 font=FONT_BOLD).pack(anchor="w", padx=18, pady=(28, 5))
        tk.Label(right, text="Stock is reduced automatically when an order is checked out.",
                 bg=PANEL, fg=MUTED, wraplength=205, justify="left",
                 font=FONT_SMALL).pack(anchor="w", padx=18)

    def action_button(self, parent, text, command):
        return tk.Button(parent, text=text, command=command, anchor="w",
                         bg=ACCENT_LIGHT, fg=ACCENT, activebackground="#D9E8FF",
                         activeforeground=NAVY, relief="flat", bd=0,
                         padx=12, pady=11, font=FONT_BOLD, cursor="hand2")

    # -------------------------------- New order -------------------------------

    def page_order(self):
        root = tk.Frame(self.content, bg=BG)
        root.pack(fill="both", expand=True)
        left = tk.Frame(root, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 16))
        right = tk.Frame(root, bg=PANEL, width=350,
                         highlightbackground=BORDER, highlightthickness=1)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        top = tk.Frame(left, bg=BG)
        top.pack(fill="x", pady=(0, 12))
        tk.Label(top, text="Choose dishes", bg=BG, fg=NAVY,
                 font=("Helvetica", 14, "bold")).pack(side="left")
        self.search_var = tk.StringVar()
        search = ttk.Entry(top, textvariable=self.search_var, width=25)
        search.pack(side="right")
        search.insert(0, "")
        search.bind("<KeyRelease>", lambda e: self.refresh_food_grid())

        self.category_var = tk.StringVar(value="All")
        category_bar = tk.Frame(left, bg=BG)
        category_bar.pack(fill="x", pady=(0, 12))
        self.category_buttons = []
        self.refresh_categories(category_bar)

        self.food_area = tk.Frame(left, bg=BG)
        self.food_area.pack(fill="both", expand=True)
        self.refresh_food_grid()

        tk.Label(right, text="Current order", bg=PANEL, fg=NAVY,
                 font=("Helvetica", 15, "bold")).pack(anchor="w", padx=17, pady=(17, 2))
        tk.Label(right, text="Adjust quantities before checkout", bg=PANEL,
                 fg=MUTED, font=FONT_SMALL).pack(anchor="w", padx=17, pady=(0, 12))
        self.cart_area = tk.Frame(right, bg=PANEL)
        self.cart_area.pack(fill="both", expand=True, padx=12)
        self.cart_total_label = tk.Label(right, text="Total  ₹0.00", bg=PANEL,
                                         fg=NAVY, font=("Helvetica", 16, "bold"))
        self.cart_total_label.pack(anchor="e", padx=18, pady=(8, 12))
        tk.Button(right, text="CHECKOUT  →", command=self.checkout,
                  bg=GREEN, fg="white", activebackground="#117B58",
                  activeforeground="white", relief="flat", bd=0,
                  font=("Helvetica", 11, "bold"), pady=13,
                  cursor="hand2").pack(fill="x", padx=15, pady=(0, 8))
        tk.Button(right, text="Clear order", command=self.clear_cart,
                  bg=PANEL, fg=RED, activebackground="#FFF0F0",
                  relief="flat", bd=0, font=FONT_BOLD, pady=8,
                  cursor="hand2").pack(fill="x", padx=15, pady=(0, 10))
        self.refresh_cart()

    def refresh_categories(self, parent):
        for child in parent.winfo_children():
            child.destroy()
        for cat in self.db.categories():
            selected = self.category_var.get() == cat
            b = tk.Button(
                parent, text=cat, command=lambda c=cat: self.select_category(c),
                bg=ACCENT if selected else PANEL,
                fg="white" if selected else MUTED,
                activebackground=ACCENT, activeforeground="white",
                relief="flat", bd=0, padx=13, pady=7, font=FONT_BOLD,
                cursor="hand2"
            )
            b.pack(side="left", padx=(0, 6))

    def select_category(self, category):
        self.category_var.set(category)
        for child in self.content.winfo_children():
            pass
        # Rebuild category buttons without rebuilding the whole order page.
        for child in self.food_area.master.winfo_children():
            if child.winfo_class() == "Frame":
                pass
        # Category buttons are the second child in the left panel.
        left = self.food_area.master
        category_bar = left.winfo_children()[1]
        self.refresh_categories(category_bar)
        self.refresh_food_grid()

    def refresh_food_grid(self):
        if not hasattr(self, "food_area") or not self.food_area.winfo_exists():
            return
        for child in self.food_area.winfo_children():
            child.destroy()
        query = self.search_var.get().strip().lower()
        dishes = self.db.dishes(self.category_var.get())
        dishes = [d for d in dishes if query in d["name"].lower()]
        if not dishes:
            tk.Label(self.food_area, text="No dishes found. Add dishes in Menu & Dishes.",
                     bg=BG, fg=MUTED, font=FONT).pack(pady=30)
            return
        canvas = tk.Canvas(self.food_area, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.food_area, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        columns = 3
        for index, dish in enumerate(dishes):
            r, c = divmod(index, columns)
            card = tk.Frame(inner, bg=PANEL, highlightbackground=BORDER,
                            highlightthickness=1, padx=12, pady=11)
            card.grid(row=r, column=c, sticky="nsew", padx=5, pady=5)
            inner.grid_columnconfigure(c, weight=1, minsize=145)
            tk.Label(card, text=dish["category"].upper(), bg=PANEL,
                     fg=ACCENT, font=("Helvetica", 8, "bold")).pack(anchor="w")
            tk.Label(card, text=dish["name"], bg=PANEL, fg=NAVY,
                     font=("Helvetica", 11, "bold"), wraplength=160,
                     justify="left").pack(anchor="w", pady=(7, 3))
            tk.Label(card, text=money(dish["price"]), bg=PANEL, fg=TEXT,
                     font=FONT_BOLD).pack(anchor="w")
            stock_text = f"In stock: {dish['stock']}"
            tk.Label(card, text=stock_text, bg=PANEL,
                     fg=RED if dish["stock"] <= 5 else MUTED,
                     font=FONT_SMALL).pack(anchor="w", pady=(3, 8))
            add = tk.Button(card, text="+ Add", command=lambda d=dish: self.add_to_cart(d["id"]),
                            bg=ACCENT_LIGHT, fg=ACCENT, activebackground="#D9E8FF",
                            relief="flat", bd=0, font=FONT_BOLD, pady=6,
                            cursor="hand2", state="normal" if dish["stock"] > 0 else "disabled")
            add.pack(fill="x")

    def add_to_cart(self, dish_id):
        dish = next((d for d in self.db.dishes(include_inactive=False) if d["id"] == dish_id), None)
        if not dish:
            return
        current = self.cart.get(dish_id, {}).get("qty", 0)
        if current >= dish["stock"]:
            messagebox.showwarning("Stock limit", f"Only {dish['stock']} units of {dish['name']} are available.")
            return
        if dish_id not in self.cart:
            self.cart[dish_id] = {"name": dish["name"], "price": dish["price"], "qty": 0}
        self.cart[dish_id]["qty"] += 1
        self.refresh_cart()

    def change_qty(self, dish_id, delta):
        if dish_id not in self.cart:
            return
        new_qty = self.cart[dish_id]["qty"] + delta
        if new_qty <= 0:
            del self.cart[dish_id]
        else:
            dish = next((d for d in self.db.dishes() if d["id"] == dish_id), None)
            if not dish or new_qty > dish["stock"]:
                messagebox.showwarning("Stock limit", "The requested quantity is more than the available stock.")
                return
            self.cart[dish_id]["qty"] = new_qty
        self.refresh_cart()

    def refresh_cart(self):
        if not hasattr(self, "cart_area") or not self.cart_area.winfo_exists():
            return
        for child in self.cart_area.winfo_children():
            child.destroy()
        total = 0
        if not self.cart:
            tk.Label(self.cart_area, text="Your order is empty.\nAdd dishes to get started.",
                     bg=PANEL, fg=MUTED, font=FONT, justify="center").pack(pady=35)
        for dish_id, item in list(self.cart.items()):
            line_total = item["qty"] * item["price"]
            total += line_total
            row = tk.Frame(self.cart_area, bg="#F8FAFD", padx=8, pady=8)
            row.pack(fill="x", pady=4)
            top = tk.Frame(row, bg="#F8FAFD")
            top.pack(fill="x")
            tk.Label(top, text=item["name"], bg="#F8FAFD", fg=NAVY,
                     font=FONT_BOLD, wraplength=205, justify="left").pack(side="left")
            tk.Label(top, text=money(line_total), bg="#F8FAFD", fg=TEXT,
                     font=FONT_BOLD).pack(side="right")
            bottom = tk.Frame(row, bg="#F8FAFD")
            bottom.pack(fill="x", pady=(7, 0))
            tk.Button(bottom, text="−", width=3,
                      command=lambda i=dish_id: self.change_qty(i, -1),
                      bg=PANEL, fg=NAVY, relief="flat", cursor="hand2").pack(side="left")
            tk.Label(bottom, text=str(item["qty"]), bg="#F8FAFD",
                     fg=NAVY, font=FONT_BOLD, width=4).pack(side="left")
            tk.Button(bottom, text="+", width=3,
                      command=lambda i=dish_id: self.change_qty(i, 1),
                      bg=PANEL, fg=NAVY, relief="flat", cursor="hand2").pack(side="left")
            tk.Label(bottom, text=f"{money(item['price'])} each", bg="#F8FAFD",
                     fg=MUTED, font=FONT_SMALL).pack(side="right")
        self.cart_total_label.configure(text=f"Total  {money(total)}")

    def clear_cart(self):
        if self.cart and messagebox.askyesno("Clear order", "Remove all items from this order?"):
            self.cart.clear()
            self.refresh_cart()

    def checkout(self):
        if not self.cart:
            messagebox.showinfo("Empty order", "Add at least one dish before checkout.")
            return
        payment = simpledialog.askstring(
            "Payment method", "Enter payment method (Cash / Card / UPI):",
            initialvalue="Cash", parent=self
        )
        if payment is None:
            return
        payment = payment.strip().title()
        if payment not in ("Cash", "Card", "Upi"):
            messagebox.showwarning("Payment method", "Please enter Cash, Card, or UPI.")
            return
        try:
            order_id, total = self.db.checkout(self.cart, payment)
        except ValueError as exc:
            messagebox.showerror("Unable to checkout", str(exc))
            self.refresh_food_grid()
            return
        receipt_lines = [f"Order #{order_id}", datetime.now().strftime("%d-%m-%Y %I:%M %p"), ""]
        for item in self.cart.values():
            receipt_lines.append(f"{item['name']}  x{item['qty']}   {money(item['qty'] * item['price'])}")
        receipt_lines += ["", f"TOTAL: {money(total)}", f"Payment: {payment}"]
        self.cart.clear()
        messagebox.showinfo("Order completed", "\n".join(receipt_lines))
        self.show_page("New Order")

    # ------------------------------ Menu / dishes ----------------------------

    def page_menu(self):
        top = tk.Frame(self.content, bg=BG)
        top.pack(fill="x", pady=(0, 13))
        tk.Label(top, text="Manage the dishes available for ordering.",
                 bg=BG, fg=MUTED, font=FONT).pack(side="left")
        tk.Button(top, text="＋  Add new dish", command=self.open_dish_dialog,
                  bg=ACCENT, fg="white", activebackground="#1D63C2",
                  activeforeground="white", relief="flat", bd=0,
                  padx=16, pady=9, font=FONT_BOLD,
                  cursor="hand2").pack(side="right")
        wrap, tree = self.make_tree(
            self.content, ("id", "name", "category", "price", "stock"),
            ("ID", "Dish name", "Category", "Price", "Current stock"),
            (65, 260, 180, 130, 130), 15
        )
        wrap.pack(fill="both", expand=True)
        for d in self.db.dishes():
            tree.insert("", "end", iid=str(d["id"]), values=(
                d["id"], d["name"], d["category"], money(d["price"]), d["stock"]
            ))
        actions = tk.Frame(self.content, bg=BG)
        actions.pack(fill="x", pady=(12, 0))
        tk.Button(actions, text="Edit selected dish", command=lambda: self.edit_selected_dish(tree),
                  bg=ACCENT_LIGHT, fg=ACCENT, relief="flat", padx=13, pady=8,
                  font=FONT_BOLD, cursor="hand2").pack(side="left")
        tk.Button(actions, text="Remove selected dish", command=lambda: self.remove_selected_dish(tree),
                  bg="#FFF0F0", fg=RED, relief="flat", padx=13, pady=8,
                  font=FONT_BOLD, cursor="hand2").pack(side="left", padx=8)

    def open_dish_dialog(self, dish=None):
        dialog = tk.Toplevel(self)
        dialog.title("Add new dish" if dish is None else "Edit dish")
        dialog.configure(bg=PANEL)
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.geometry("390x390")
        tk.Label(dialog, text="Dish details", bg=PANEL, fg=NAVY,
                 font=("Helvetica", 16, "bold")).pack(anchor="w", padx=22, pady=(20, 15))

        fields = {}
        values = {
            "Dish name": dish["name"] if dish else "",
            "Category": dish["category"] if dish else "Main Course",
            "Price (₹)": str(dish["price"]) if dish else "",
            "Opening stock": str(dish["stock"]) if dish else "0",
        }
        for label, value in values.items():
            tk.Label(dialog, text=label, bg=PANEL, fg=TEXT,
                     font=FONT_BOLD).pack(anchor="w", padx=22, pady=(7, 3))
            entry = ttk.Entry(dialog, width=38)
            entry.pack(padx=22, fill="x")
            entry.insert(0, value)
            fields[label] = entry

        def save():
            name = fields["Dish name"].get().strip()
            category = fields["Category"].get().strip()
            try:
                price = float(fields["Price (₹)"].get())
                stock = int(fields["Opening stock"].get())
                if not name or not category or price < 0 or stock < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid details", "Enter a dish name, category, valid price and whole-number stock.", parent=dialog)
                return
            try:
                if dish:
                    self.db.update_dish(dish["id"], name, category, price, stock)
                else:
                    self.db.add_dish(name, category, price, stock)
            except sqlite3.IntegrityError:
                messagebox.showerror("Duplicate dish", "A dish with this name already exists.", parent=dialog)
                return
            dialog.destroy()
            self.show_page(self.current_page)

        tk.Button(dialog, text="SAVE DISH", command=save, bg=ACCENT, fg="white",
                  relief="flat", bd=0, font=FONT_BOLD, pady=10,
                  cursor="hand2").pack(fill="x", padx=22, pady=20)

    def selected_dish(self, tree):
        selection = tree.selection()
        if not selection:
            messagebox.showinfo("Select a dish", "Please select a dish first.")
            return None
        dish_id = int(selection[0])
        return next((d for d in self.db.dishes(include_inactive=True) if d["id"] == dish_id), None)

    def edit_selected_dish(self, tree):
        dish = self.selected_dish(tree)
        if dish:
            self.open_dish_dialog(dish)

    def remove_selected_dish(self, tree):
        dish = self.selected_dish(tree)
        if dish and messagebox.askyesno("Remove dish", f"Remove {dish['name']} from the active menu?"):
            self.db.delete_dish(dish["id"])
            self.show_page("Menu & Dishes")

    # -------------------------------- Inventory -------------------------------

    def page_inventory(self):
        top = tk.Frame(self.content, bg=BG)
        top.pack(fill="x", pady=(0, 13))
        tk.Label(top, text="Monitor available ingredients / dish quantities.",
                 bg=BG, fg=MUTED, font=FONT).pack(side="left")
        tk.Button(top, text="＋  Add stock", command=self.open_stock_dialog,
                  bg=GREEN, fg="white", activebackground="#117B58",
                  activeforeground="white", relief="flat", bd=0,
                  padx=16, pady=9, font=FONT_BOLD,
                  cursor="hand2").pack(side="right")
        wrap, tree = self.make_tree(
            self.content, ("id", "name", "category", "stock", "status"),
            ("ID", "Dish name", "Category", "Available units", "Stock status"),
            (65, 260, 180, 150, 150), 15
        )
        wrap.pack(fill="both", expand=True)
        for d in self.db.dishes():
            status = "LOW STOCK" if d["stock"] <= 5 else "In stock"
            tree.insert("", "end", iid=str(d["id"]), values=(
                d["id"], d["name"], d["category"], d["stock"], status
            ))
            if d["stock"] <= 5:
                tree.item(str(d["id"]), tags=("low",))
        tree.tag_configure("low", foreground=RED)
        actions = tk.Frame(self.content, bg=BG)
        actions.pack(fill="x", pady=(12, 0))
        tk.Button(actions, text="＋ Add stock to selected dish",
                  command=lambda: self.open_stock_dialog(tree),
                  bg=ACCENT_LIGHT, fg=ACCENT, relief="flat", padx=13, pady=8,
                  font=FONT_BOLD, cursor="hand2").pack(side="left")

    def open_stock_dialog(self, tree=None):
        dishes = self.db.dishes()
        if not dishes:
            messagebox.showinfo("No dishes", "Add a dish before adding stock.")
            return
        dialog = tk.Toplevel(self)
        dialog.title("Add stock")
        dialog.configure(bg=PANEL)
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.geometry("390x265")
        tk.Label(dialog, text="Add inventory", bg=PANEL, fg=NAVY,
                 font=("Helvetica", 16, "bold")).pack(anchor="w", padx=22, pady=(20, 15))
        options = {f"{d['name']}  (current: {d['stock']})": d["id"] for d in dishes}
        selected = tk.StringVar()
        if tree and tree.selection():
            chosen_id = int(tree.selection()[0])
            selected.set(next((k for k, v in options.items() if v == chosen_id), list(options)[0]))
        else:
            selected.set(list(options)[0])
        tk.Label(dialog, text="Select dish", bg=PANEL, fg=TEXT, font=FONT_BOLD).pack(anchor="w", padx=22)
        combo = ttk.Combobox(dialog, textvariable=selected, values=list(options), state="readonly", width=37)
        combo.pack(padx=22, fill="x", pady=(4, 12))
        tk.Label(dialog, text="Quantity to add", bg=PANEL, fg=TEXT, font=FONT_BOLD).pack(anchor="w", padx=22)
        amount = ttk.Entry(dialog, width=38)
        amount.pack(padx=22, fill="x", pady=(4, 10))
        amount.insert(0, "10")

        def save():
            try:
                qty = int(amount.get())
                if qty <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid quantity", "Enter a whole number greater than zero.", parent=dialog)
                return
            self.db.update_stock(options[selected.get()], qty)
            dialog.destroy()
            self.show_page("Inventory")

        tk.Button(dialog, text="UPDATE STOCK", command=save, bg=GREEN, fg="white",
                  relief="flat", bd=0, font=FONT_BOLD, pady=10,
                  cursor="hand2").pack(fill="x", padx=22, pady=14)

    # ------------------------------- Sales history ----------------------------

    def page_sales(self):
        stats = self.db.sales_summary()
        summary = tk.Frame(self.content, bg=BG)
        summary.pack(fill="x", pady=(0, 18))
        for title, value, sub, color in [
            ("All-time revenue", money(stats["all_sales"]), "Total recorded sales", ACCENT),
            ("Orders completed", str(stats["all_orders"]), "All-time order count", GREEN),
        ]:
            self.card(summary, title, value, sub, color).pack(
                side="left", fill="both", expand=True, padx=(0, 12)
            )
        self.section_title(self.content, "Transaction history", "Select an order and view its item details.")
        wrap, tree = self.make_tree(
            self.content, ("id", "date", "payment", "total"),
            ("Order ID", "Date & Time", "Payment method", "Total"),
            (90, 260, 170, 150), 11
        )
        wrap.pack(fill="both", expand=True)
        for row in self.db.recent_orders(200):
            tree.insert("", "end", iid=str(row["id"]), values=(
                f"#{row['id']}", row["created_at"], row["payment_method"], money(row["total"])
            ))
        tk.Button(self.content, text="View selected order details",
                  command=lambda: self.view_order(tree),
                  bg=ACCENT_LIGHT, fg=ACCENT, relief="flat", padx=14, pady=9,
                  font=FONT_BOLD, cursor="hand2").pack(anchor="w", pady=12)

    def view_order(self, tree):
        selection = tree.selection()
        if not selection:
            messagebox.showinfo("Select an order", "Please select an order first.")
            return
        order_id = int(selection[0])
        items = self.db.order_items(order_id)
        lines = [f"Order #{order_id}", ""]
        for item in items:
            lines.append(
                f"{item['dish_name']}  x{item['quantity']}  "
                f"{money(item['unit_price'] * item['quantity'])}"
            )
        messagebox.showinfo("Order details", "\n".join(lines))

    def on_close(self):
        self.db.close()
        self.destroy()


if __name__ == "__main__":
    app = RestaurantPOS()
    app.mainloop()
