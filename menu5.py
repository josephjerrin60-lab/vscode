"""
RestroBit - Restaurant Point of Sale (POS)
-----------------------------------------
A complete, mouse-driven restaurant order-taking program built with Tkinter
(Python standard library only - nothing to install).

Run:   python restrobit_pos.py

Features
  * POS screen   : category chips, search, click a dish to add it, + / - quantity,
                   notes per item, discount, tax, KOT, draft, bill & payment, receipt
  * Dashboard    : sales KPIs, 7-day sales chart, top dishes, recent orders, low stock
  * Stock        : live stock table, add stock count, edit / delete dish
  * Add new dish : name, category (existing or new), price, opening stock, icon
Data is saved automatically in restrobit.db (SQLite) next to this script.
"""

import os
import random
import sqlite3
import datetime as dt
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# ----------------------------------------------------------------- settings
CURRENCY = "₹"          # Indian rupee
TAX_RATE = 0.05         # 5 % tax
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "restrobit.db")
OUT_DIR = os.path.dirname(DB_FILE)

ORANGE = "#F97316"
DARK = "#111827"
GREEN = "#16A34A"
RED = "#DC2626"
BG = "#F8F8F8"
WHITE = "#FFFFFF"
BORDER = "#E5E7EB"
GREY = "#6B7280"
LIGHT_ORANGE = "#FFEDD5"

FONT = "Segoe UI"


def money(v):
    return f"{CURRENCY}{v:,.2f}"


# ----------------------------------------------------------------- menu
# Dishes with {"Quarter":..,"Half":..,"Full":..} prices become one menu item per size.
MENU = {
    "Starters": {
        "Samosa": 30,
        "Chicken 65": 170,
        "French Fries": 100,
        "Paneer Tikka": 150,
        "Hot & sour soap": 80,
        "Mutton soup": 120,
    },
    "Main Course": {
        "Chicken Biriyani": 190,
        "Porotta & Beef Roast": 160,
        "Appam & Pork Fry": 180,
        "Butter Naan & Butter Chicken": 200,
        "Alfahm mandi quarter": 120,
        "kabsa fry": 100,
        "Mutton biriyani": 250,
        "Paalkappa & beef": 180,
    },
    "Breads": {
        "Porotta": 15,
        "Naan": 30,
        "Garlic Naan": 45,
        "Butter Naan": 40,
        "Romali Roti": 25,
    },
    "Grills": {
        "Normal Alfaham":       {"Quarter": 120, "Half": 230, "Full": 440},
        "Peri Peri Alfaham":    {"Quarter": 140, "Half": 270, "Full": 520},
        "Honey Chilli Alfaham": {"Quarter": 150, "Half": 290, "Full": 550},
        "Afghani Alfaham":      {"Quarter": 160, "Half": 310, "Full": 590},
        "Normal BBQ":           {"Quarter": 110, "Half": 210, "Full": 400},
        "Peri Peri BBQ":        {"Quarter": 130, "Half": 250, "Full": 480},
        "Arabic BBQ":           {"Quarter": 140, "Half": 270, "Full": 520},
    },
    "Desserts": {
        "Gulab Jamun": 60,
        "Ice Cream": 70,
        "Payasam": 50,
        "Brownie with Ice Cream": 110,
    },
    "Juice and Shakes": {
        "Orange Juice": 60,
        "Watermelon Juice": 50,
        "Mango Shake": 80,
        "Fresh Lime Soda": 40,
        "Oreo shake": 90,
        "Kitkat shake": 100,
        "Darkfantasy shake": 100,
        "Chocolate shake": 80,
        "Chickoo shake": 80,
        "Sharjah shake": 80,
    },
}
CATEGORY_EMOJI = {"Starters": "🍤", "Main Course": "🍛", "Breads": "🍞", "Grills": "🍗",
                  "Desserts": "🍨", "Juice and Shakes": "🥤"}
ITEM_EMOJI = {"Samosa": "🥟", "French Fries": "🍟", "Chicken 65": "🍗", "Paneer Tikka": "🧀",
              "Hot & sour soap": "🍲", "Mutton soup": "🍲", "Chicken Biriyani": "🍚", "Mutton biriyani": "🍚",
              "Ice Cream": "🍦", "Gulab Jamun": "🍮", "Orange Juice": "🍊", "Watermelon Juice": "🍉",
              "Mango Shake": "🥭", "Fresh Lime Soda": "🍋", "Normal BBQ": "🍖", "Peri Peri BBQ": "🍖",
              "Arabic BBQ": "🍖"}
START_STOCK = {"Starters": 50, "Main Course": 40, "Breads": 100, "Grills": 30,
               "Desserts": 40, "Juice and Shakes": 60}


def menu_to_dishes():
    """Flatten MENU into (name, category, price, stock, emoji) rows."""
    rows = []
    for cat, items in MENU.items():
        for name, price in items.items():
            emoji = ITEM_EMOJI.get(name, CATEGORY_EMOJI[cat])
            if isinstance(price, dict):
                for size, p in price.items():
                    rows.append((f"{name} ({size})", cat, p, START_STOCK[cat], emoji))
            else:
                rows.append((name, cat, price, START_STOCK[cat], emoji))
    return rows


def mix(color, amount):
    """Lighten (+) or darken (-) a #RRGGBB colour for hover effects."""
    r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
    f = lambda c: max(0, min(255, int(c + (255 - c) * amount if amount > 0 else c * (1 + amount))))
    return "#%02x%02x%02x" % (f(r), f(g), f(b))


# ----------------------------------------------------------------- database
class Database:
    def __init__(self, path=DB_FILE):
        self.con = sqlite3.connect(path)
        self.con.row_factory = sqlite3.Row
        # menu version 2 = new menu: wipe the old demo menu/sales from earlier versions once
        if self.con.execute("PRAGMA user_version").fetchone()[0] < 2:
            self.con.executescript("DROP TABLE IF EXISTS dishes; DROP TABLE IF EXISTS sales; "
                                   "DROP TABLE IF EXISTS sale_items;")
            self.con.execute("PRAGMA user_version = 2")
        self.con.executescript("""
        CREATE TABLE IF NOT EXISTS dishes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL, category TEXT NOT NULL,
            price REAL NOT NULL, stock INTEGER NOT NULL, emoji TEXT DEFAULT '🍽️');
        CREATE TABLE IF NOT EXISTS sales(
            id INTEGER PRIMARY KEY AUTOINCREMENT, created TEXT, dining TEXT, tbl TEXT,
            subtotal REAL, discount REAL, tax REAL, total REAL, payment TEXT);
        CREATE TABLE IF NOT EXISTS sale_items(
            sale_id INTEGER, name TEXT, qty INTEGER, price REAL);
        """)
        if self.con.execute("SELECT COUNT(*) FROM dishes").fetchone()[0] == 0:
            self.seed()

    def q(self, sql, args=()):
        return self.con.execute(sql, args).fetchall()

    def run(self, sql, args=()):
        cur = self.con.execute(sql, args)
        self.con.commit()
        return cur

    def seed(self):
        dishes = menu_to_dishes()
        self.con.executemany("INSERT INTO dishes(name,category,price,stock,emoji) VALUES(?,?,?,?,?)", dishes)
        # sample sales history so the dashboard looks alive on first run
        today = dt.datetime.now()
        for d in range(13, -1, -1):
            for _ in range(random.randint(4, 10)):
                when = (today - dt.timedelta(days=d)).replace(hour=random.randint(11, 22),
                                                              minute=random.randint(0, 59), second=0)
                items = random.sample(dishes, random.randint(1, 4))
                lines = [(n, random.randint(1, 3), p) for n, c, p, s, e in items]
                sub = sum(q * p for n, q, p in lines)
                tax = round(sub * TAX_RATE, 2)
                cur = self.con.execute(
                    "INSERT INTO sales(created,dining,tbl,subtotal,discount,tax,total,payment) VALUES(?,?,?,?,?,?,?,?)",
                    (when.strftime("%Y-%m-%d %H:%M:%S"), random.choice(["Dine In", "Take Away", "Delivery"]),
                     f"Table {random.randint(1, 12)}", sub, 0, tax, sub + tax,
                     random.choice(["Cash", "Card", "UPI"])))
                self.con.executemany("INSERT INTO sale_items VALUES(?,?,?,?)",
                                     [(cur.lastrowid, n, q, p) for n, q, p in lines])
        self.con.commit()


# ----------------------------------------------------------------- widgets
class Btn(tk.Label):
    """Flat clickable button that looks the same on Windows / macOS / Linux."""

    def __init__(self, parent, text, command, bg=WHITE, fg=DARK, border=True,
                 font=(FONT, 10, "bold"), padx=14, pady=8, **kw):
        super().__init__(parent, text=text, bg=bg, fg=fg, font=font, padx=padx, pady=pady,
                         cursor="hand2", highlightthickness=1 if border else 0,
                         highlightbackground=BORDER, **kw)
        self.base, self.command = bg, command
        self.bind("<Button-1>", lambda e: self.command())
        self.bind("<Enter>", lambda e: self.config(bg=mix(self.base, -0.08 if self.base != WHITE else -0.04)))
        self.bind("<Leave>", lambda e: self.config(bg=self.base))


class ScrollFrame(tk.Frame):
    """Vertically scrollable frame (mouse-wheel handled globally by the App)."""

    def __init__(self, parent, bg=WHITE):
        super().__init__(parent, bg=bg)
        self._is_scroll = True
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        sb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=bg)
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.win, width=e.width))
        self.canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

    def clear(self):
        for w in self.inner.winfo_children():
            w.destroy()


def bind_click(widget, fn):
    widget.bind("<Button-1>", lambda e: fn())
    for c in widget.winfo_children():
        bind_click(c, fn)


def card(parent, **kw):
    return tk.Frame(parent, bg=WHITE, highlightthickness=1, highlightbackground=BORDER, **kw)


# ----------------------------------------------------------------- dialogs
class DishDialog(tk.Toplevel):
    """Add a new dish or edit an existing one."""

    def __init__(self, app, dish=None):
        super().__init__(app)
        self.app, self.dish = app, dish
        self.title("Edit Dish" if dish else "Add New Dish")
        self.configure(bg=WHITE, padx=24, pady=20)
        self.resizable(False, False)
        self.transient(app)
        self.grab_set()

        cats = sorted({r["category"] for r in app.db.q("SELECT category FROM dishes")})
        self.v_name = tk.StringVar(value=dish["name"] if dish else "")
        self.v_cat = tk.StringVar(value=dish["category"] if dish else (cats[0] if cats else ""))
        self.v_price = tk.StringVar(value=str(dish["price"]) if dish else "")
        self.v_stock = tk.StringVar(value=str(dish["stock"]) if dish else "0")
        self.v_emoji = tk.StringVar(value=dish["emoji"] if dish else "🍽️")

        tk.Label(self, text=self.title(), font=(FONT, 15, "bold"), bg=WHITE, fg=DARK).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 14))
        rows = [("Dish name", ttk.Entry(self, textvariable=self.v_name, width=32)),
                ("Category (pick or type new)", ttk.Combobox(self, textvariable=self.v_cat, values=cats, width=30)),
                (f"Price ({CURRENCY})", ttk.Entry(self, textvariable=self.v_price, width=32)),
                ("Stock count", ttk.Entry(self, textvariable=self.v_stock, width=32)),
                ("Icon (any emoji)", ttk.Entry(self, textvariable=self.v_emoji, width=32))]
        for i, (lbl, w) in enumerate(rows, start=1):
            tk.Label(self, text=lbl, bg=WHITE, fg=GREY, font=(FONT, 9)).grid(row=i * 2 - 1, column=0, columnspan=2, sticky="w")
            w.grid(row=i * 2, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        Btn(self, "Save", self.save, bg=ORANGE, fg=WHITE, border=False).grid(row=12, column=0, sticky="ew", padx=(0, 6), pady=(8, 0))
        Btn(self, "Cancel", self.destroy).grid(row=12, column=1, sticky="ew", padx=(6, 0), pady=(8, 0))

    def save(self):
        name, cat = self.v_name.get().strip(), self.v_cat.get().strip()
        try:
            price, stock = float(self.v_price.get()), int(self.v_stock.get())
            assert price >= 0 and stock >= 0
        except Exception:
            return messagebox.showerror("Invalid", "Price must be a number and stock a whole number (0 or more).", parent=self)
        if not name or not cat:
            return messagebox.showerror("Invalid", "Name and category are required.", parent=self)
        emoji = self.v_emoji.get().strip() or "🍽️"
        try:
            if self.dish:
                self.app.db.run("UPDATE dishes SET name=?,category=?,price=?,stock=?,emoji=? WHERE id=?",
                                (name, cat, price, stock, emoji, self.dish["id"]))
            else:
                self.app.db.run("INSERT INTO dishes(name,category,price,stock,emoji) VALUES(?,?,?,?,?)",
                                (name, cat, price, stock, emoji))
        except sqlite3.IntegrityError:
            return messagebox.showerror("Duplicate", "A dish with that name already exists.", parent=self)
        self.destroy()
        self.app.refresh_all()


def text_window(app, title, text, filename):
    """Show a KOT / receipt in a window with a Save-&-Print button."""
    win = tk.Toplevel(app)
    win.title(title)
    win.configure(bg=WHITE, padx=16, pady=16)
    win.transient(app)
    box = tk.Text(win, width=44, height=26, font=("Courier New", 10), bg="#FFFDF7", fg="black",
                  relief="flat", highlightthickness=1, highlightbackground=BORDER)
    box.insert("1.0", text)
    box.tag_configure("default", foreground="black")
    box.tag_add("default", "1.0", "end")
    box.config(state="disabled")
    box.pack()

    def do_print():
        path = os.path.join(OUT_DIR, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        try:
            if os.name == "nt":
                os.startfile(path, "print")
        except Exception:
            pass
        messagebox.showinfo("Saved", f"Saved to:\n{path}", parent=win)

    bar = tk.Frame(win, bg=WHITE)
    bar.pack(fill="x", pady=(10, 0))
    Btn(bar, "🖨  Print / Save", do_print, bg=GREEN, fg=WHITE, border=False).pack(side="left", expand=True, fill="x", padx=(0, 5))
    Btn(bar, "Close", win.destroy).pack(side="left", expand=True, fill="x", padx=(5, 0))


# ----------------------------------------------------------------- main app
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RestroBit – Restaurant POS")
        self.geometry("1380x820")
        self.minsize(1200, 700)
        self.configure(bg=BG)
        self.db = Database()

        self.cart = {}          # dish_id -> qty
        self.notes = {}         # dish_id -> note text
        self.drafts = []        # saved draft orders (kept while the app is open)
        self.category = "Show All"
        self.discount = 0.0

        st = ttk.Style(self)
        try:
            st.theme_use("clam")
        except tk.TclError:
            pass
        st.configure("Treeview", rowheight=32, font=(FONT, 10), background=WHITE, fieldbackground=WHITE, borderwidth=0)
        st.configure("Treeview.Heading", font=(FONT, 10, "bold"), background="#F3F4F6", foreground=DARK, relief="flat")
        st.map("Treeview", background=[("selected", LIGHT_ORANGE)], foreground=[("selected", DARK)])
        st.configure("TCombobox", padding=6)

        self.build_sidebar()
        self.content = tk.Frame(self, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)

        self.pages = {
            "dashboard": tk.Frame(self.content, bg=BG),
            "pos": tk.Frame(self.content, bg=BG),
            "stock": tk.Frame(self.content, bg=BG),
        }
        self.build_pos()
        self.build_stock()
        self.bind_all("<MouseWheel>", self.on_wheel)
        self.bind_all("<Button-4>", self.on_wheel)
        self.bind_all("<Button-5>", self.on_wheel)
        self.show("pos")

    # ---------------------------------------------------------- navigation
    def build_sidebar(self):
        sb = tk.Frame(self, bg=WHITE, width=250, highlightthickness=1, highlightbackground=BORDER)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)
        tk.Label(sb, text="⬢ RestroBit", font=(FONT, 20, "bold"), bg=WHITE, fg=ORANGE).pack(pady=(24, 18))

        user = tk.Frame(sb, bg=WHITE)
        user.pack(fill="x", padx=18, pady=(0, 16))
        tk.Label(user, text="👤", font=(FONT, 22), bg=WHITE).pack(side="left")
        info = tk.Frame(user, bg=WHITE)
        info.pack(side="left", padx=8)
        tk.Label(info, text="Waiter / Cashier", font=(FONT, 11, "bold"), bg=WHITE, fg=DARK).pack(anchor="w")
        tk.Label(info, text="Order Desk", font=(FONT, 9), bg=WHITE, fg=GREY).pack(anchor="w")

        self.nav = {}
        items = [("dashboard", "📊   Dashboard"), ("pos", "🧾   POS / New Order"), ("stock", "📦   Stock & Dishes")]
        for key, label in items:
            b = tk.Label(sb, text=label, anchor="w", font=(FONT, 11), bg=WHITE, fg=DARK, padx=16, pady=11, cursor="hand2")
            b.pack(fill="x", padx=14, pady=2)
            b.bind("<Button-1>", lambda e, k=key: self.show(k))
            self.nav[key] = b

        tk.Label(sb, text="Quick actions", font=(FONT, 9), bg=WHITE, fg=GREY).pack(anchor="w", padx=22, pady=(18, 4))
        for label, cmd in [("➕   Add New Dish", lambda: DishDialog(self)),
                           ("📥   Add Stock Count", lambda: (self.show("stock"), self.add_stock_count()))]:
            b = tk.Label(sb, text=label, anchor="w", font=(FONT, 11), bg=WHITE, fg=DARK, padx=16, pady=11, cursor="hand2")
            b.pack(fill="x", padx=14, pady=2)
            b.bind("<Button-1>", lambda e, c=cmd: c())

        ex = tk.Label(sb, text="⎋   Exit", anchor="w", font=(FONT, 11), bg=WHITE, fg=GREY, padx=16, pady=11, cursor="hand2")
        ex.pack(side="bottom", fill="x", padx=14, pady=16)
        ex.bind("<Button-1>", lambda e: self.destroy())

    def show(self, key):
        for k, p in self.pages.items():
            p.pack_forget()
        for k, b in self.nav.items():
            b.config(bg=LIGHT_ORANGE if k == key else WHITE, fg=ORANGE if k == key else DARK,
                     font=(FONT, 11, "bold" if k == key else "normal"))
        self.pages[key].pack(fill="both", expand=True, padx=26, pady=20)
        if key == "dashboard":
            self.build_dashboard()
        elif key == "stock":
            self.refresh_stock()
        elif key == "pos":
            self.render_products()

    def on_wheel(self, e):
        try:
            w = self.winfo_containing(e.x_root, e.y_root)
        except Exception:
            return
        while w is not None:
            if getattr(w, "_is_scroll", False):
                d = -1 if (e.num == 4 or getattr(e, "delta", 0) > 0) else 1
                w.canvas.yview_scroll(d, "units")
                return
            w = w.master

    def refresh_all(self):
        self.render_chips()
        self.render_products()
        self.render_cart()
        self.refresh_stock()

    # ---------------------------------------------------------- POS page
    def build_pos(self):
        page = self.pages["pos"]
        head = tk.Frame(page, bg=BG)
        head.pack(fill="x")
        left = tk.Frame(head, bg=BG)
        left.pack(side="left")
        tk.Label(left, text="Point of Sale (POS)", font=(FONT, 20, "bold"), bg=BG, fg=DARK).pack(anchor="w")
        tk.Label(left, text="Dashboard  •  Pos", font=(FONT, 9), bg=BG, fg=GREY).pack(anchor="w")
        Btn(head, "📋 Draft List", self.show_drafts).pack(side="right", padx=4)
        Btn(head, "＋ New", self.new_order, bg=ORANGE, fg=WHITE, border=False).pack(side="right", padx=4)

        body = tk.Frame(page, bg=BG)
        body.pack(fill="both", expand=True, pady=(14, 0))

        # ---- product panel
        prod = card(body)
        prod.pack(side="left", fill="both", expand=True, padx=(0, 14))
        top = tk.Frame(prod, bg=WHITE)
        top.pack(fill="x", padx=16, pady=14)
        tk.Label(top, text="🔍", bg=WHITE).pack(side="left")
        self.v_search = tk.StringVar()
        self.v_search.trace_add("write", lambda *a: self.render_products())
        ttk.Entry(top, textvariable=self.v_search, font=(FONT, 11)).pack(side="left", fill="x", expand=True, padx=6, ipady=4)
        tk.Frame(prod, bg=BORDER, height=1).pack(fill="x")
        self.chips = tk.Frame(prod, bg=WHITE)
        self.chips.pack(fill="x", padx=16, pady=12)
        self.grid_area = ScrollFrame(prod)
        self.grid_area.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # ---- order panel
        order = card(body, width=400)
        order.pack(side="right", fill="y")
        order.pack_propagate(False)
        sel = tk.Frame(order, bg=WHITE)
        sel.pack(fill="x", padx=14, pady=(14, 6))
        self.v_dining = tk.StringVar(value="Dine In")
        self.v_table = tk.StringVar(value="Select Table")
        d = ttk.Combobox(sel, textvariable=self.v_dining, values=["Dine In", "Take Away", "Delivery"], state="readonly", width=14)
        d.pack(side="left", expand=True, fill="x", padx=(0, 6))
        t = ttk.Combobox(sel, textvariable=self.v_table, values=[f"Table {i}" for i in range(1, 13)],
                         state="readonly", width=14)
        t.pack(side="left", expand=True, fill="x")
        self.cb_table = t
        d.bind("<<ComboboxSelected>>", lambda e: self.cb_table.config(
            state="readonly" if self.v_dining.get() == "Dine In" else "disabled"))

        self.lbl_order = tk.Label(order, font=(FONT, 13, "bold"), bg=WHITE, fg=DARK)
        self.lbl_order.pack(anchor="w", padx=16, pady=(6, 4))

        # bottom first so the cart gets the remaining space
        bottom = tk.Frame(order, bg=WHITE)
        bottom.pack(side="bottom", fill="x", padx=14, pady=14)
        row1 = tk.Frame(bottom, bg=WHITE)
        row1.pack(fill="x", pady=(0, 8))
        Btn(row1, "KOT & Print", self.kot, bg=DARK, fg=WHITE, border=False).pack(side="left", expand=True, fill="x", padx=(0, 6))
        Btn(row1, "Draft", self.save_draft).pack(side="left", padx=(0, 6))
        Btn(row1, "Clear", self.clear_cart, fg=RED).pack(side="left")
        row2 = tk.Frame(bottom, bg=WHITE)
        row2.pack(fill="x")
        Btn(row2, "Bill & Payment", self.pay_dialog, bg=ORANGE, fg=WHITE, border=False).pack(side="left", expand=True, fill="x", padx=(0, 6))
        Btn(row2, "Bill & Print", lambda: self.checkout("Cash"), bg=GREEN, fg=WHITE, border=False).pack(side="left", expand=True, fill="x")

        tot = tk.Frame(order, bg=WHITE)
        tot.pack(side="bottom", fill="x", padx=16, pady=(6, 0))
        self.totals = {}
        for key, label in [("sub", "Sub total :"), ("disc", "Discount :"), ("tax", f"Tax ({int(TAX_RATE * 100)}%) :"), ("total", "Total :")]:
            r = tk.Frame(tot, bg=WHITE)
            r.pack(fill="x", pady=2)
            bold = key == "total"
            tk.Label(r, text=label, bg=WHITE, fg=DARK, font=(FONT, 12 if bold else 10, "bold" if bold else "normal")).pack(side="left")
            lbl = tk.Label(r, bg=WHITE, fg=DARK, font=(FONT, 12 if bold else 10, "bold" if bold else "normal"))
            lbl.pack(side="right")
            if key == "disc":
                lbl.config(cursor="hand2", fg=ORANGE)
                lbl.bind("<Button-1>", lambda e: self.set_discount())
            self.totals[key] = lbl
        tk.Frame(order, bg=BORDER, height=1).pack(side="bottom", fill="x", pady=(8, 0))

        self.cart_area = ScrollFrame(order)
        self.cart_area.pack(fill="both", expand=True, padx=10)

        self.render_chips()
        self.render_products()
        self.render_cart()

    def categories(self):
        return [r["category"] for r in self.db.q("SELECT category FROM dishes GROUP BY category ORDER BY MIN(id)")]

    def render_chips(self):
        for w in self.chips.winfo_children():
            w.destroy()
        cats = ["Show All"] + self.categories()
        if self.category not in cats:
            self.category = "Show All"
        for c in cats:
            on = c == self.category
            Btn(self.chips, c, lambda c=c: self.set_category(c), bg=ORANGE if on else WHITE,
                fg=WHITE if on else DARK, border=not on, font=(FONT, 10), padx=9, pady=5).pack(side="left", padx=3)

    def set_category(self, c):
        self.category = c
        self.render_chips()
        self.render_products()

    def render_products(self):
        g = self.grid_area
        g.clear()
        sql, args = "SELECT * FROM dishes WHERE name LIKE ?", [f"%{self.v_search.get().strip()}%"]
        if self.category != "Show All":
            sql += " AND category=?"
            args.append(self.category)
        dishes = self.db.q(sql + " ORDER BY id", args)
        cols = 4
        for c in range(cols):
            g.inner.columnconfigure(c, weight=1, uniform="col")
        if not dishes:
            tk.Label(g.inner, text="No dishes found", bg=WHITE, fg=GREY, font=(FONT, 11)).grid(pady=40)
        for i, d in enumerate(dishes):
            in_cart = self.cart.get(d["id"], 0)
            out = d["stock"] - in_cart <= 0
            c = tk.Frame(g.inner, bg=WHITE, highlightthickness=2 if in_cart else 1,
                         highlightbackground=ORANGE if in_cart else BORDER, cursor="hand2")
            c.grid(row=i // cols, column=i % cols, padx=6, pady=6, sticky="nsew")
            tk.Label(c, text=d["emoji"], font=("Segoe UI Emoji", 34), bg=WHITE).pack(pady=(14, 4))
            tk.Label(c, text=d["name"], font=(FONT, 10), bg=WHITE, fg=DARK, wraplength=130).pack()
            tk.Label(c, text=money(d["price"]), font=(FONT, 11, "bold"), bg=WHITE, fg=RED).pack(pady=(2, 0))
            left = d["stock"] - in_cart
            tk.Label(c, text="Out of stock" if out else f"{left} in stock", font=(FONT, 8), bg=WHITE,
                     fg=RED if out or left <= 10 else GREY).pack(pady=(0, 6))
            if in_cart:
                tk.Label(c, text=f"× {in_cart} in order", font=(FONT, 8, "bold"), bg=LIGHT_ORANGE, fg=ORANGE,
                         padx=6).pack(pady=(0, 8))
            if not out:
                bind_click(c, lambda did=d["id"]: self.change_qty(did, 1))

    # ---------------------------------------------------------- cart logic
    def dish(self, did):
        r = self.db.q("SELECT * FROM dishes WHERE id=?", (did,))
        return r[0] if r else None

    def change_qty(self, did, delta):
        d = self.dish(did)
        if not d:
            return
        new = self.cart.get(did, 0) + delta
        if new > d["stock"]:
            return messagebox.showwarning("Stock", f"Only {d['stock']} of '{d['name']}' left in stock.")
        if new <= 0:
            self.cart.pop(did, None)
            self.notes.pop(did, None)
        else:
            self.cart[did] = new
        self.render_cart()
        self.render_products()

    def render_cart(self):
        nxt = (self.db.q("SELECT IFNULL(MAX(id),0)+1 AS n FROM sales")[0]["n"])
        self.lbl_order.config(text=f"🛍  Order #{nxt}")
        a = self.cart_area
        a.clear()
        if not self.cart:
            tk.Label(a.inner, text="No items yet.\nClick a dish to add it.", bg=WHITE, fg=GREY,
                     font=(FONT, 10)).pack(pady=50)
        for did, qty in self.cart.items():
            d = self.dish(did)
            r = tk.Frame(a.inner, bg=WHITE, highlightthickness=1, highlightbackground=BORDER)
            r.pack(fill="x", padx=4, pady=5)
            top = tk.Frame(r, bg=WHITE)
            top.pack(fill="x", padx=12, pady=(10, 0))
            tk.Label(top, text=f"{d['emoji']} {d['name']}", font=(FONT, 11), bg=WHITE, fg=DARK).pack(side="left")
            Btn(top, "✕", lambda did=did: self.change_qty(did, -9999), bg="#FEE2E2", fg=RED, border=False,
                padx=7, pady=1).pack(side="right")
            tk.Label(r, text=f"{money(d['price'])} × {qty} = {money(d['price'] * qty)}", font=(FONT, 10, "bold"),
                     bg=WHITE, fg=ORANGE).pack(anchor="w", padx=12, pady=2)
            if self.notes.get(did):
                tk.Label(r, text=f"📝 {self.notes[did]}", font=(FONT, 9, "italic"), bg=WHITE, fg=GREY,
                         wraplength=320, justify="left").pack(anchor="w", padx=12)
            ctl = tk.Frame(r, bg=WHITE)
            ctl.pack(fill="x", padx=12, pady=(2, 10))
            Btn(ctl, "−", lambda did=did: self.change_qty(did, -1), padx=9, pady=1, font=(FONT, 11, "bold")).pack(side="left")
            tk.Label(ctl, text=str(qty), width=3, font=(FONT, 11, "bold"), bg=WHITE).pack(side="left")
            Btn(ctl, "+", lambda did=did: self.change_qty(did, 1), bg=ORANGE, fg=WHITE, border=False,
                padx=9, pady=1, font=(FONT, 11, "bold")).pack(side="left")
            Btn(ctl, "📝 Add Notes", lambda did=did: self.add_note(did), font=(FONT, 9), padx=8, pady=2).pack(side="right")
        self.update_totals()

    def add_note(self, did):
        n = simpledialog.askstring("Notes", "Special instructions (e.g. less spicy):",
                                   initialvalue=self.notes.get(did, ""), parent=self)
        if n is not None:
            self.notes[did] = n.strip()
            self.render_cart()

    def calc(self):
        sub = sum(self.dish(i)["price"] * q for i, q in self.cart.items())
        disc = min(self.discount, sub)
        tax = round((sub - disc) * TAX_RATE, 2)
        return sub, disc, tax, sub - disc + tax

    def update_totals(self):
        sub, disc, tax, total = self.calc()
        self.totals["sub"].config(text=money(sub))
        self.totals["disc"].config(text=f"✎ {money(disc)}")
        self.totals["tax"].config(text=money(tax))
        self.totals["total"].config(text=money(total))

    def set_discount(self):
        v = simpledialog.askfloat("Discount", f"Discount amount ({CURRENCY}):", initialvalue=self.discount,
                                  minvalue=0, parent=self)
        if v is not None:
            self.discount = v
            self.update_totals()

    def clear_cart(self, ask=True):
        if ask and self.cart and not messagebox.askyesno("Clear", "Remove all items from this order?"):
            return
        self.cart.clear()
        self.notes.clear()
        self.discount = 0.0
        self.v_table.set("Select Table")
        self.render_cart()
        self.render_products()

    def new_order(self):
        if self.cart and not messagebox.askyesno("New order", "Discard the current order and start a new one?"):
            return
        self.clear_cart(ask=False)

    # ---------------------------------------------------------- drafts
    def save_draft(self):
        if not self.cart:
            return messagebox.showinfo("Draft", "Add some items first.")
        self.drafts.append(dict(cart=dict(self.cart), notes=dict(self.notes), dining=self.v_dining.get(),
                                table=self.v_table.get(), discount=self.discount,
                                time=dt.datetime.now().strftime("%H:%M")))
        self.clear_cart(ask=False)
        messagebox.showinfo("Draft", "Order saved as draft.")

    def show_drafts(self):
        win = tk.Toplevel(self)
        win.title("Draft List")
        win.configure(bg=WHITE, padx=16, pady=16)
        win.transient(self)
        tk.Label(win, text="Draft Orders", font=(FONT, 14, "bold"), bg=WHITE).pack(anchor="w", pady=(0, 8))
        if not self.drafts:
            tk.Label(win, text="No drafts saved.", bg=WHITE, fg=GREY).pack(pady=20, padx=40)
        for i, d in enumerate(self.drafts):
            r = tk.Frame(win, bg=WHITE, highlightthickness=1, highlightbackground=BORDER)
            r.pack(fill="x", pady=4)
            n = sum(d["cart"].values())
            tk.Label(r, text=f"Draft {i + 1}  •  {n} items  •  {d['dining']}  •  {d['time']}", bg=WHITE,
                     font=(FONT, 10)).pack(side="left", padx=10, pady=10)
            Btn(r, "Load", lambda i=i, w=win: self.load_draft(i, w), bg=ORANGE, fg=WHITE, border=False, pady=3).pack(side="right", padx=8)

    def load_draft(self, i, win):
        if self.cart and not messagebox.askyesno("Load draft", "Replace the current order?", parent=win):
            return
        d = self.drafts.pop(i)
        self.cart, self.notes, self.discount = d["cart"], d["notes"], d["discount"]
        self.v_dining.set(d["dining"])
        self.v_table.set(d["table"])
        win.destroy()
        self.render_cart()
        self.render_products()

    # ---------------------------------------------------------- KOT / billing
    def order_lines(self):
        return [(self.dish(i), q) for i, q in self.cart.items()]

    def header_text(self, title):
        order_no = self.db.q("SELECT IFNULL(MAX(id),0)+1 AS n FROM sales")[0]["n"]
        tbl = self.v_table.get() if self.v_dining.get() == "Dine In" else "-"
        return order_no, ("=" * 38 + f"\n{title:^38}\n" + "=" * 38 +
                          f"\nOrder #{order_no}    {dt.datetime.now():%d-%m-%Y %H:%M}\n"
                          f"{self.v_dining.get()}   {tbl}\n" + "-" * 38 + "\n")

    def check_ready(self):
        if not self.cart:
            messagebox.showinfo("Order", "The order is empty.")
            return False
        if self.v_dining.get() == "Dine In" and self.v_table.get() == "Select Table":
            messagebox.showwarning("Table", "Please select a table for a Dine-In order.")
            return False
        return True

    def kot(self):
        if not self.check_ready():
            return
        no, txt = self.header_text("KITCHEN ORDER TICKET")
        for d, q in self.order_lines():
            txt += f"{q:>3} x {d['name']}\n"
            if self.notes.get(d["id"]):
                txt += f"      >> {self.notes[d['id']]}\n"
        text_window(self, "KOT", txt, f"kot_{no}.txt")

    def pay_dialog(self):
        if not self.check_ready():
            return
        sub, disc, tax, total = self.calc()
        win = tk.Toplevel(self)
        win.title("Payment")
        win.configure(bg=WHITE, padx=26, pady=22)
        win.transient(self)
        win.grab_set()
        tk.Label(win, text="Amount to pay", bg=WHITE, fg=GREY, font=(FONT, 10)).pack()
        tk.Label(win, text=money(total), bg=WHITE, fg=DARK, font=(FONT, 26, "bold")).pack(pady=(0, 14))
        for m, icon in [("Cash", "💵"), ("Card", "💳"), ("UPI", "📱")]:
            Btn(win, f"{icon}  Pay by {m}", lambda m=m: (win.destroy(), self.checkout(m)),
                bg=ORANGE, fg=WHITE, border=False, pady=10).pack(fill="x", pady=4)
        Btn(win, "Cancel", win.destroy).pack(fill="x", pady=(8, 0))

    def checkout(self, payment):
        if not self.check_ready():
            return
        sub, disc, tax, total = self.calc()
        lines = self.order_lines()
        for d, q in lines:                               # final stock check
            if q > d["stock"]:
                return messagebox.showerror("Stock", f"Not enough stock for {d['name']}.")
        now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tbl = self.v_table.get() if self.v_dining.get() == "Dine In" else "-"
        cur = self.db.run("INSERT INTO sales(created,dining,tbl,subtotal,discount,tax,total,payment) VALUES(?,?,?,?,?,?,?,?)",
                          (now, self.v_dining.get(), tbl, sub, disc, tax, total, payment))
        for d, q in lines:
            self.db.con.execute("INSERT INTO sale_items VALUES(?,?,?,?)", (cur.lastrowid, d["name"], q, d["price"]))
            self.db.con.execute("UPDATE dishes SET stock=stock-? WHERE id=?", (q, d["id"]))
        self.db.con.commit()

        txt = ("=" * 38 + f"\n{'RESTROBIT':^38}\n{'Thank you for dining with us':^38}\n" + "=" * 38 +
               f"\nBill #{cur.lastrowid}    {dt.datetime.now():%d-%m-%Y %H:%M}\n{self.v_dining.get()}   {tbl}\n"
               + "-" * 38 + "\n")
        for d, q in lines:
            txt += f"{d['name'][:20]:<20}{q:>3} x {d['price']:>6.2f}{d['price'] * q:>7.2f}\n"
        txt += ("-" * 38 + f"\n{'Sub total':<28}{sub:>10.2f}\n{'Discount':<28}{-disc:>10.2f}\n"
                f"{'Tax':<28}{tax:>10.2f}\n" + "=" * 38 + f"\n{'TOTAL (' + CURRENCY + ')':<28}{total:>10.2f}\n"
                f"Paid by: {payment}\n" + "=" * 38)
        self.clear_cart(ask=False)
        self.refresh_all()
        text_window(self, "Receipt", txt, f"bill_{cur.lastrowid}.txt")

    # ---------------------------------------------------------- stock page
    def build_stock(self):
        page = self.pages["stock"]
        head = tk.Frame(page, bg=BG)
        head.pack(fill="x")
        left = tk.Frame(head, bg=BG)
        left.pack(side="left")
        tk.Label(left, text="Stock & Dishes", font=(FONT, 20, "bold"), bg=BG, fg=DARK).pack(anchor="w")
        tk.Label(left, text="Dashboard  •  Stock", font=(FONT, 9), bg=BG, fg=GREY).pack(anchor="w")
        Btn(head, "🗑 Delete", self.delete_dish, fg=RED).pack(side="right", padx=4)
        Btn(head, "✎ Edit Dish", self.edit_dish).pack(side="right", padx=4)
        Btn(head, "📥 Add Stock Count", self.add_stock_count, bg=DARK, fg=WHITE, border=False).pack(side="right", padx=4)
        Btn(head, "＋ Add New Dish", lambda: DishDialog(self), bg=ORANGE, fg=WHITE, border=False).pack(side="right", padx=4)

        box = card(page)
        box.pack(fill="both", expand=True, pady=(14, 0))
        bar = tk.Frame(box, bg=WHITE)
        bar.pack(fill="x", padx=14, pady=12)
        tk.Label(bar, text="🔍", bg=WHITE).pack(side="left")
        self.v_ssearch = tk.StringVar()
        self.v_ssearch.trace_add("write", lambda *a: self.refresh_stock())
        ttk.Entry(bar, textvariable=self.v_ssearch, font=(FONT, 11), width=40).pack(side="left", padx=6, ipady=3)
        self.lbl_low = tk.Label(bar, bg=WHITE, fg=RED, font=(FONT, 10, "bold"))
        self.lbl_low.pack(side="right")

        cols = ("id", "name", "category", "price", "stock", "status")
        self.tree = ttk.Treeview(box, columns=cols, show="headings", selectmode="browse")
        for c, w, a in [("id", 50, "center"), ("name", 260, "w"), ("category", 140, "w"),
                        ("price", 100, "e"), ("stock", 100, "center"), ("status", 140, "center")]:
            self.tree.heading(c, text=c.title())
            self.tree.column(c, width=w, anchor=a)
        sb = ttk.Scrollbar(box, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True, padx=(14, 0), pady=(0, 14))
        self.tree.tag_configure("low", foreground="#B45309")
        self.tree.tag_configure("out", foreground=RED)
        self.tree.bind("<Double-1>", lambda e: self.add_stock_count())

    def refresh_stock(self):
        self.tree.delete(*self.tree.get_children())
        like = f"%{self.v_ssearch.get().strip()}%"
        low = 0
        for r in self.db.q("SELECT * FROM dishes WHERE name LIKE ? OR category LIKE ? ORDER BY id", (like, like)):
            status, tag = "In stock", ""
            if r["stock"] == 0:
                status, tag, low = "Out of stock", "out", low + 1
            elif r["stock"] <= 10:
                status, tag, low = "Low stock", "low", low + 1
            self.tree.insert("", "end", iid=str(r["id"]), tags=(tag,),
                             values=(r["id"], f"{r['emoji']}  {r['name']}", r["category"], money(r["price"]),
                                     r["stock"], status))
        self.lbl_low.config(text=f"⚠ {low} item(s) low / out of stock" if low else "")

    def selected_dish(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Click a dish in the table first.")
            return None
        return self.dish(int(sel[0]))

    def add_stock_count(self):
        d = self.selected_dish()
        if not d:
            return
        n = simpledialog.askinteger("Add stock", f"Add how many units to '{d['name']}'?\n(Current stock: {d['stock']})",
                                    minvalue=1, parent=self)
        if n:
            self.db.run("UPDATE dishes SET stock=stock+? WHERE id=?", (n, d["id"]))
            self.refresh_all()

    def edit_dish(self):
        d = self.selected_dish()
        if d:
            DishDialog(self, d)

    def delete_dish(self):
        d = self.selected_dish()
        if d and messagebox.askyesno("Delete", f"Delete '{d['name']}' from the menu?"):
            self.cart.pop(d["id"], None)
            self.db.run("DELETE FROM dishes WHERE id=?", (d["id"],))
            self.refresh_all()

    # ---------------------------------------------------------- dashboard
    def reset_dashboard(self):
        if not messagebox.askyesno("Reset dashboard", "Reset all sales history to zero? This clears the dashboard totals."):
            return
        self.db.run("DELETE FROM sale_items")
        self.db.run("DELETE FROM sales")
        self.db.run("DELETE FROM sqlite_sequence WHERE name='sales'")
        self.clear_cart(ask=False)
        self.build_dashboard()
        messagebox.showinfo("Dashboard reset", "Dashboard totals have been reset to ₹0.00.")

    def build_dashboard(self):
        page = self.pages["dashboard"]
        for w in page.winfo_children():
            w.destroy()
        head = tk.Frame(page, bg=BG)
        head.pack(fill="x")
        left = tk.Frame(head, bg=BG)
        left.pack(side="left")
        tk.Label(left, text="Dashboard", font=(FONT, 20, "bold"), bg=BG, fg=DARK).pack(anchor="w")
        tk.Label(left, text=f"Sales overview  •  {dt.datetime.now():%A, %d %B %Y}", font=(FONT, 9),
                 bg=BG, fg=GREY).pack(anchor="w")
        Btn(head, "Reset to 0", self.reset_dashboard, bg=RED, fg=WHITE, border=False).pack(side="right")

        today = dt.date.today().isoformat()
        q1 = lambda sql, a=(): self.db.q(sql, a)[0][0] or 0
        kpis = [
            ("Today's Sales", money(q1("SELECT SUM(total) FROM sales WHERE substr(created,1,10)=?", (today,))), "💰", ORANGE),
            ("Today's Orders", str(q1("SELECT COUNT(*) FROM sales WHERE substr(created,1,10)=?", (today,))), "🧾", "#2563EB"),
            ("Total Revenue", money(q1("SELECT SUM(total) FROM sales")), "📈", GREEN),
            ("Avg. Order Value", money(q1("SELECT AVG(total) FROM sales")), "🧮", "#7C3AED"),
            ("Low / Out of Stock", str(q1("SELECT COUNT(*) FROM dishes WHERE stock<=10")), "⚠️", RED),
        ]
        row = tk.Frame(page, bg=BG)
        row.pack(fill="x", pady=14)
        for i, (t, v, ic, col) in enumerate(kpis):
            row.columnconfigure(i, weight=1, uniform="k")
            c = card(row)
            c.grid(row=0, column=i, sticky="nsew", padx=6)
            tk.Frame(c, bg=col, height=4).pack(fill="x")
            tk.Label(c, text=f"{ic}  {t}", font=(FONT, 10), bg=WHITE, fg=GREY).pack(anchor="w", padx=14, pady=(12, 0))
            tk.Label(c, text=v, font=(FONT, 20, "bold"), bg=WHITE, fg=DARK).pack(anchor="w", padx=14, pady=(2, 14))

        mid = tk.Frame(page, bg=BG)
        mid.pack(fill="both", expand=True)
        mid.columnconfigure(0, weight=3)
        mid.columnconfigure(1, weight=2)
        mid.rowconfigure(0, weight=1)

        # sales bar chart (last 7 days)
        c1 = card(mid)
        c1.grid(row=0, column=0, sticky="nsew", padx=6)
        tk.Label(c1, text="Sales – last 7 days", font=(FONT, 12, "bold"), bg=WHITE).pack(anchor="w", padx=14, pady=(12, 0))
        days = [(dt.date.today() - dt.timedelta(days=i)) for i in range(6, -1, -1)]
        data = {r[0]: r[1] for r in self.db.q("SELECT substr(created,1,10), SUM(total) FROM sales GROUP BY 1")}
        vals = [(d.strftime("%a"), data.get(d.isoformat(), 0)) for d in days]
        cv = tk.Canvas(c1, bg=WHITE, highlightthickness=0)
        cv.pack(fill="both", expand=True, padx=10, pady=10)
        cv.bind("<Configure>", lambda e: self.draw_bars(cv, vals))

        right = tk.Frame(mid, bg=BG)
        right.grid(row=0, column=1, sticky="nsew", padx=6)
        right.rowconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        c2 = card(right)
        c2.grid(row=0, column=0, sticky="nsew", pady=(0, 6))
        tk.Label(c2, text="Top selling dishes", font=(FONT, 12, "bold"), bg=WHITE).pack(anchor="w", padx=14, pady=(12, 6))
        top = self.db.q("SELECT name, SUM(qty) q FROM sale_items GROUP BY name ORDER BY q DESC LIMIT 5")
        mx = top[0]["q"] if top else 1
        for r in top:
            f = tk.Frame(c2, bg=WHITE)
            f.pack(fill="x", padx=14, pady=3)
            tk.Label(f, text=r["name"], bg=WHITE, font=(FONT, 9), width=18, anchor="w").pack(side="left")
            bar = tk.Canvas(f, height=14, bg=WHITE, highlightthickness=0)
            bar.pack(side="left", fill="x", expand=True)
            bar.bind("<Configure>", lambda e, b=bar, v=r["q"]: (b.delete("all"),
                     b.create_rectangle(0, 2, max(4, (e.width - 4) * v / mx), 12, fill=ORANGE, outline="")))
            tk.Label(f, text=str(r["q"]), bg=WHITE, font=(FONT, 9, "bold"), width=5).pack(side="left")

        c3 = card(right)
        c3.grid(row=1, column=0, sticky="nsew", pady=(6, 0))
        tk.Label(c3, text="Recent orders", font=(FONT, 12, "bold"), bg=WHITE).pack(anchor="w", padx=14, pady=(12, 4))
        t = ttk.Treeview(c3, columns=("id", "time", "type", "total"), show="headings", height=5)
        for c, w in [("id", 45), ("time", 110), ("type", 80), ("total", 80)]:
            t.heading(c, text=c.title())
            t.column(c, width=w, anchor="center")
        for r in self.db.q("SELECT * FROM sales ORDER BY id DESC LIMIT 8"):
            t.insert("", "end", values=(f"#{r['id']}", r["created"][5:16], r["dining"], money(r["total"])))
        t.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def draw_bars(self, cv, vals):
        cv.delete("all")
        w, h = cv.winfo_width(), cv.winfo_height()
        if w < 50 or h < 50:
            return
        mx = max(v for _, v in vals) or 1
        left, bottom, top = 50, h - 28, 20
        for i in range(5):
            y = bottom - (bottom - top) * i / 4
            cv.create_line(left, y, w - 10, y, fill="#F3F4F6")
            cv.create_text(left - 6, y, text=f"{CURRENCY}{mx * i / 4:,.0f}", anchor="e", font=(FONT, 8), fill=GREY)
        slot = (w - left - 10) / len(vals)
        for i, (lab, v) in enumerate(vals):
            x0 = left + i * slot + slot * 0.2
            x1 = left + (i + 1) * slot - slot * 0.2
            y = bottom - (bottom - top) * v / mx
            cv.create_rectangle(x0, y, x1, bottom, fill=ORANGE if i == len(vals) - 1 else "#FDBA74", outline="")
            cv.create_text((x0 + x1) / 2, y - 8, text=f"{v:,.0f}", font=(FONT, 8, "bold"), fill=DARK)
            cv.create_text((x0 + x1) / 2, bottom + 14, text=lab, font=(FONT, 9), fill=GREY)


if __name__ == "__main__":
    App().mainloop()
