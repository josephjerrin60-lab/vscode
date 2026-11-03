# Restaurant Billing System - POS style GUI (tkinter)
import math
import sys
import textwrap
import tkinter as tk
from tkinter import font as tkfont, messagebox, ttk
from datetime import datetime

RESTAURANT_NAME = "PARAGON"   # change this to your restaurant's name

# Normal items -> price (int)
# Grill items  -> {size: price} (dictionary)
menu = {
    "Starters": {
        "Samosa": 30,
        "Chicken 65": 170,
        "French Fries": 100,
        "Paneer Tikka": 150,
        "Hot & sour soap":80,
        "Mutton soup":120,

    },
    "Main Course": {
        "Chicken Biriyani": 190,
        "Porotta & Beef Roast": 160,
        "Appam & Pork Fry": 180,
        "Butter Naan & Butter Chicken": 200,
        "Alfahm mandi quarter": 120,
        "kabsa fry":100,
        "Mutton biriyani": 250,
        "Paalkappa & beef":180,

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

GST_RATE = 0.05  # 5% GST

# ---------------- Colours (change these to restyle the app) ----------------
PAGE = "#f4f5f7"
WHITE = "#ffffff"
BORDER = "#e5e7eb"
TEXT = "#1f2937"
MUTED = "#6b7280"
ORANGE = "#f97316"
ORANGE_HOVER = "#fb8a3c"
PRICE = "#e8452c"
DARK = "#111827"
GRAY = "#f3f4f6"
GRAY_HOVER = "#e5e7eb"
RED = "#ef4444"
RED_SOFT = "#fee2e2"
SHADOW = "#e2e5ea"
ROW_BG = "#fafafa"

# (soft background, accent) for the round "photo" placeholder on each card
CAT_STYLE = {
    "Starters":    ("#ffedd5", "#ea580c"),
    "Main Course": ("#fee2e2", "#dc2626"),
    "Breads":      ("#fef3c7", "#d97706"),
    "Grills":      ("#ede9fe", "#7c3aed"),
    "Desserts":    ("#fce7f3", "#db2777"),
    "Juice and Shakes":      ("#dcfce7", "#16a34a"),
}

F = {}  # fonts, filled in once the window exists


def init_fonts():
    avail = set(tkfont.families())

    def pick(*names):
        for n in names:
            if n in avail:
                return n
        return names[-1]

    sans = pick("Inter", "Helvetica Neue", "Segoe UI", "Helvetica", "DejaVu Sans")
    mono = pick("Courier New", "Menlo", "Courier", "DejaVu Sans Mono")
    F.update(
        h1=(sans, 20, "bold"), brand=(sans, 18, "bold"), h2=(sans, 15, "bold"),
        body=(sans, 12), body_b=(sans, 12, "bold"), small=(sans, 11),
        tiny=(sans, 10), card=(sans, 12), price=(sans, 13, "bold"),
        btn=(sans, 13, "bold"), total=(sans, 16, "bold"),
        initial=(sans, 24, "bold"), mono=(mono, 12), mono_b=(mono, 12, "bold"),
    )
    F["measure"] = tkfont.Font(family=sans, size=12, weight="bold")
    F["measure_btn"] = tkfont.Font(family=sans, size=13, weight="bold")


# ---------------- Drawing helpers ----------------
def round_rect(c, x1, y1, x2, y2, r, **kw):
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
           x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return c.create_polygon(pts, smooth=True, **kw)


class Panel(tk.Canvas):
    """A white rounded card. Put child widgets inside panel.body."""

    def __init__(self, parent, width=None, height=None, radius=14, pad=6,
                 fill=WHITE, border=BORDER, shadow=False):
        size = {}
        if width:
            size["width"] = width
        if height:
            size["height"] = height
        super().__init__(parent, bg=parent["bg"], highlightthickness=0, **size)
        self.radius, self.pad, self.fill = radius, pad, fill
        self.border, self.shadow = border, shadow
        self.body = tk.Frame(self, bg=fill)
        self.win = self.create_window(pad, pad, window=self.body, anchor="nw")
        self.bind("<Configure>", self._redraw)

    def _redraw(self, event=None):
        w, h = self.winfo_width(), self.winfo_height()
        self.delete("bg")
        s = 4 if self.shadow else 0
        if self.shadow:
            round_rect(self, 3, 5, w - 1, h - 1, self.radius,
                       fill=SHADOW, outline="", tags="bg")
        round_rect(self, 1, 1, w - 1 - s, h - 1 - s, self.radius,
                   fill=self.fill, outline=self.border, tags="bg")
        self.tag_lower("bg")
        self.itemconfig(self.win, width=max(1, w - 2 * self.pad - s),
                        height=max(1, h - 2 * self.pad - s))

    def set_border(self, color):
        self.border = color
        self._redraw()


class RoundButton(tk.Canvas):
    def __init__(self, parent, text, command, width, height, radius=8,
                 fill=GRAY, hover=GRAY_HOVER, fg=TEXT, outline="", font=None):
        super().__init__(parent, width=width, height=height, bg=parent["bg"],
                         highlightthickness=0, cursor="hand2")
        self.command, self.fill, self.hover = command, fill, hover
        self.shape = round_rect(self, 1, 1, width - 1, height - 1, radius,
                                fill=fill, outline=outline)
        self.label = self.create_text(width / 2, height / 2, text=text,
                                      fill=fg, font=font or F["btn"],
                                      justify="center")
        self.bind("<Button-1>", lambda e: self.command())
        self.bind("<Enter>", lambda e: self.itemconfig(self.shape, fill=self.hover))
        self.bind("<Leave>", lambda e: self.itemconfig(self.shape, fill=self.fill))

    def restyle(self, fill, hover, fg):
        self.fill, self.hover = fill, hover
        self.itemconfig(self.shape, fill=fill)
        self.itemconfig(self.label, fill=fg)


class CircleButton(tk.Canvas):
    """Small round icon button: plus, minus or trash."""

    def __init__(self, parent, size, fill, hover, command, icon, color):
        super().__init__(parent, width=size, height=size, bg=parent["bg"],
                         highlightthickness=0, cursor="hand2")
        self.fill, self.hover, self.command = fill, hover, command
        self.oval = self.create_oval(1, 1, size - 1, size - 1, fill=fill, outline="")
        c = size / 2
        if icon in ("plus", "minus"):
            self.create_line(c - 5, c, c + 5, c, fill=color, width=2, capstyle="round")
            if icon == "plus":
                self.create_line(c, c - 5, c, c + 5, fill=color, width=2, capstyle="round")
        elif icon == "trash":
            self.create_line(c - 5, c - 3, c + 5, c - 3, fill=color, width=2, capstyle="round")
            self.create_line(c - 2, c - 6, c + 2, c - 6, fill=color, width=2, capstyle="round")
            self.create_polygon(c - 4, c - 1, c + 4, c - 1, c + 3, c + 6, c - 3, c + 6,
                                outline=color, fill="", width=2)
        self.bind("<Button-1>", lambda e: self.command())
        self.bind("<Enter>", lambda e: self.itemconfig(self.oval, fill=self.hover))
        self.bind("<Leave>", lambda e: self.itemconfig(self.oval, fill=self.fill))


class SearchBox(Panel):
    """Rounded text field with a placeholder."""

    def __init__(self, parent, placeholder, on_change=None, width=None,
                 height=42, icon=True):
        super().__init__(parent, width=width, height=height, radius=9, pad=4)
        self.on_change = on_change
        self.var = tk.StringVar()
        if icon:
            ic = tk.Canvas(self.body, width=22, height=22, bg=WHITE, highlightthickness=0)
            ic.create_oval(4, 4, 14, 14, outline=MUTED, width=2)
            ic.create_line(13, 13, 18, 18, fill=MUTED, width=2, capstyle="round")
            ic.pack(side="left", padx=(10, 2))
        self.entry = tk.Entry(self.body, textvariable=self.var, relief="flat", bd=0,
                              highlightthickness=0, bg=WHITE, fg=TEXT,
                              insertbackground=TEXT, font=F["body"])
        self.entry.pack(side="left", fill="both", expand=True,
                        padx=(0 if icon else 10, 6), pady=6)
        self.hint = tk.Label(self.body, text=placeholder, bg=WHITE, fg=MUTED,
                             font=F["body"])
        self.hint.place(in_=self.entry, x=2, rely=0.5, anchor="w")
        self.hint.bind("<Button-1>", lambda e: self.entry.focus_set())
        self.entry.bind("<FocusIn>", self._focus_in)
        self.entry.bind("<FocusOut>", self._focus_out)
        self.var.trace_add("write", self._changed)

    def _focus_in(self, e):
        self.hint.place_forget()
        self.set_border(ORANGE)

    def _focus_out(self, e):
        self.set_border(BORDER)
        if not self.var.get():
            self.hint.place(in_=self.entry, x=2, rely=0.5, anchor="w")

    def _changed(self, *args):
        if self.var.get():
            self.hint.place_forget()
        elif self.focus_get() is not self.entry:
            self.hint.place(in_=self.entry, x=2, rely=0.5, anchor="w")
        if self.on_change:
            self.on_change(self.var.get())


class ScrollFrame(tk.Frame):
    """Vertically scrollable area (mouse wheel / trackpad). Add widgets to .inner"""
    registry = []

    def __init__(self, parent, bg):
        super().__init__(parent, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, yscrollincrement=24)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.inner = tk.Frame(self.canvas, bg=bg)
        self.window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(
            self.window, width=e.width))

        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)
        self.canvas.bind("<Button-5>", self._on_mousewheel)
        ScrollFrame.registry.append(self)

    def _on_mousewheel(self, event):
        if getattr(event, "num", None) == 4:
            delta = -1
        elif getattr(event, "num", None) == 5:
            delta = 1
        elif sys.platform == "darwin":
            delta = -event.delta
        else:
            delta = -int(event.delta / 120)
        self.canvas.yview_scroll(delta, "units")
        return "break"

    def to_top(self):
        self.canvas.yview_moveto(0)


class ItemCard(tk.Canvas):
    W, H = 172, 188

    def __init__(self, parent, name, price_text, tint, accent, command):
        super().__init__(parent, width=self.W, height=self.H, bg=WHITE,
                         highlightthickness=0, cursor="hand2")
        W, H = self.W, self.H
        self.command = command
        self.shape = round_rect(self, 1, 1, W - 1, H - 1, 12, fill=WHITE, outline=BORDER)
        self.create_oval(W / 2 - 38, 14, W / 2 + 38, 90, fill=tint, outline="")
        self.create_text(W / 2, 52, text=name[0], fill=accent, font=F["initial"])
        self.create_text(W / 2, 102, text=name, anchor="n", width=W - 28,
                         justify="center", fill=TEXT, font=F["card"])
        self.create_text(16, H - 18, text=price_text, anchor="w", fill=PRICE,
                         font=F["price"])
        self.plus_bg = self.create_oval(W - 38, H - 32, W - 14, H - 8, fill=ORANGE,
                                        outline="", state="hidden")
        self.plus_fg = self.create_text(W - 26, H - 20, text="+", fill="white",
                                        font=F["btn"], state="hidden")
        self.bind("<Button-1>", lambda e: self.command())
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)

    def _enter(self, e):
        self.itemconfig(self.shape, outline="#fdba74")
        self.itemconfig(self.plus_bg, state="normal")
        self.itemconfig(self.plus_fg, state="normal")

    def _leave(self, e):
        self.itemconfig(self.shape, outline=BORDER)
        self.itemconfig(self.plus_bg, state="hidden")
        self.itemconfig(self.plus_fg, state="hidden")


def money(x):
    return f"₹{x:,.2f}"


class RestaurantApp:
    def __init__(self, root):
        init_fonts()
        self.root = root
        root.title(f"{RESTAURANT_NAME} - Billing")
        root.geometry("1280x800")
        root.minsize(1180, 740)
        root.configure(bg=PAGE)

        self.order = {}          # item name -> [price, qty]
        self.order_no = 1
        self.bill_no = 0
        self.dining = "Dine In"
        self.category = "All"
        self.query = ""
        self.cat_pills = {}
        self.dining_pills = {}
        self.sheet = None

        self.build_topbar()
        self.build_header()
        self.build_main()

        self.show_items()
        self.refresh_order()

    # ---------------- Layout ----------------
    def build_topbar(self):
        bar = tk.Frame(self.root, bg=WHITE)
        bar.pack(fill="x")
        logo = tk.Canvas(bar, width=40, height=40, bg=WHITE, highlightthickness=0)
        pts = []
        for i in range(6):
            a = math.pi / 3 * i - math.pi / 2
            pts += [20 + 17 * math.cos(a), 20 + 17 * math.sin(a)]
        logo.create_polygon(pts, fill=ORANGE, outline=ORANGE, width=3, joinstyle="round")
        logo.create_text(20, 20, text=RESTAURANT_NAME[0], fill="white", font=F["btn"])
        logo.pack(side="left", padx=(24, 8), pady=12)
        tk.Label(bar, text=RESTAURANT_NAME, font=F["brand"], bg=WHITE,
                 fg=DARK).pack(side="left")
        tk.Label(bar, text=datetime.now().strftime("%A, %d %B %Y"), font=F["small"],
                 bg=WHITE, fg=MUTED).pack(side="right", padx=24)
        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x")

    def build_header(self):
        head = tk.Frame(self.root, bg=PAGE)
        head.pack(fill="x", padx=24, pady=(18, 14))
        left = tk.Frame(head, bg=PAGE)
        left.pack(side="left")
        tk.Label(left, text="Point of Sale", font=F["h1"], bg=PAGE,
                 fg=DARK).pack(anchor="w")
        tk.Label(left, text="Menu   •   Billing", font=F["tiny"], bg=PAGE,
                 fg=MUTED).pack(anchor="w", pady=(2, 0))
        label = "+  New Order"
        RoundButton(head, label, self.new_order,
                    F["measure_btn"].measure(label) + 44, 40, radius=8,
                    fill=ORANGE, hover=ORANGE_HOVER, fg="white").pack(side="right")

    def build_main(self):
        main = tk.Frame(self.root, bg=PAGE)
        main.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        # ===== Right: order panel =====
        self.right = Panel(main, width=400)
        self.right.pack(side="right", fill="y", padx=(16, 0))
        rb = self.right.body

        row = tk.Frame(rb, bg=WHITE)
        row.pack(fill="x", padx=20, pady=(18, 10))
        for label in ("Dine In", "Takeaway", "Delivery"):
            w = F["measure"].measure(label) + 30
            b = RoundButton(row, label, lambda l=label: self.set_dining(l), w, 34,
                            radius=8, font=F["body_b"])
            b.pack(side="left", padx=(0, 8))
            self.dining_pills[label] = b

        title = tk.Frame(rb, bg=WHITE)
        title.pack(fill="x", padx=20, pady=(6, 8))
        self.order_title = tk.Label(title, text="Order #1", font=F["h2"], bg=WHITE, fg=DARK)
        self.order_title.pack(side="left")
        self.table_box = SearchBox(title, "Table no.", width=120, height=36, icon=False)
        self.table_box.pack(side="right")

        self.order_scroll = ScrollFrame(rb, WHITE)
        self.order_scroll.pack(fill="both", expand=True, padx=(20, 12), pady=(0, 6))

        tk.Frame(rb, bg=BORDER, height=1).pack(fill="x")

        tot = tk.Frame(rb, bg=WHITE)
        tot.pack(fill="x", padx=20, pady=(12, 8))
        tot.grid_columnconfigure(1, weight=1)
        self.sub_val = self._total_row(tot, 0, "Sub total", F["body"], TEXT)
        self.gst_val = self._total_row(tot, 1, f"GST ({int(GST_RATE * 100)}%)", F["body"], TEXT)
        self.total_val = self._total_row(tot, 2, "Total", F["total"], DARK)

        btns = tk.Frame(rb, bg=WHITE)
        btns.pack(fill="x", padx=20, pady=(4, 18))
        RoundButton(btns, "Clear Order", self.clear_order, 166, 46, radius=8,
                    fill=WHITE, hover=GRAY, fg=TEXT, outline=BORDER).pack(side="left")
        RoundButton(btns, "Generate Bill", self.show_bill, 166, 46, radius=8,
                    fill=ORANGE, hover=ORANGE_HOVER, fg="white").pack(side="right")

        # ===== Left: products panel =====
        self.left = Panel(main)
        self.left.pack(side="left", fill="both", expand=True)
        self.left_body = lb = self.left.body

        top = tk.Frame(lb, bg=WHITE)
        top.pack(fill="x", padx=20, pady=(18, 14))
        self.search = SearchBox(top, "Search dishes", self.on_search, height=42)
        self.search.pack(fill="x")

        tk.Frame(lb, bg=BORDER, height=1).pack(fill="x")

        pills = tk.Frame(lb, bg=WHITE)
        pills.pack(fill="x", padx=20, pady=(14, 8))
        for cat in ["All"] + list(menu):
            w = F["measure"].measure(cat) + 32
            b = RoundButton(pills, cat, lambda c=cat: self.select_category(c), w, 34,
                            radius=8, font=F["body_b"])
            b.pack(side="left", padx=(0, 8))
            self.cat_pills[cat] = b

        self.grid_scroll = ScrollFrame(lb, WHITE)
        self.grid_scroll.pack(fill="both", expand=True, padx=(20, 8), pady=(4, 12))

        self.restyle_pills()

    @staticmethod
    def _total_row(parent, r, label, font, color):
        tk.Label(parent, text=label, font=font, bg=WHITE, fg=color).grid(
            row=r, column=0, sticky="w", pady=3)
        val = tk.Label(parent, text="", font=font, bg=WHITE, fg=color)
        val.grid(row=r, column=1, sticky="e", pady=3)
        return val

    # ---------------- Pills ----------------
    def restyle_pills(self):
        for cat, b in self.cat_pills.items():
            active = (cat == self.category and not self.query)
            if active:
                b.restyle(ORANGE, ORANGE_HOVER, "white")
            else:
                b.restyle(GRAY, GRAY_HOVER, TEXT)
        for label, b in self.dining_pills.items():
            if label == self.dining:
                b.restyle(DARK, "#1f2937", "white")
            else:
                b.restyle(GRAY, GRAY_HOVER, TEXT)

    def select_category(self, cat):
        self.category = cat
        self.search.var.set("")      # also clears the search
        self.query = ""
        self.restyle_pills()
        self.show_items()

    def set_dining(self, label):
        self.dining = label
        if label == "Dine In":
            self.table_box.pack(side="right")
        else:
            self.table_box.pack_forget()
        self.restyle_pills()

    def on_search(self, text):
        self.query = text.strip().lower()
        self.restyle_pills()
        self.show_items()

    # ---------------- Product grid ----------------
    def show_items(self):
        self.hide_sheet()
        host = self.grid_scroll.inner
        for w in host.winfo_children():
            w.destroy()

        if self.query:
            items = [(c, n, p) for c, d in menu.items() for n, p in d.items()
                     if self.query in n.lower()]
        elif self.category == "All":
            items = [(c, n, p) for c, d in menu.items() for n, p in d.items()]
        else:
            items = [(self.category, n, p) for n, p in menu[self.category].items()]

        if not items:
            tk.Label(host, text=f"No dishes match “{self.query}”.\nTry a different name.",
                     font=F["body"], bg=WHITE, fg=MUTED, justify="center").pack(pady=80)
            return

        for col in range(4):
            host.grid_columnconfigure(col, weight=1)
        for i, (cat, name, price) in enumerate(items):
            if isinstance(price, dict):
                price_text = f"from ₹{min(price.values())}"
            else:
                price_text = f"₹{price}"
            tint, accent = CAT_STYLE[cat]
            card = ItemCard(host, name, price_text, tint, accent,
                            lambda n=name, p=price: self.pick_item(n, p))
            card.grid(row=i // 4, column=i % 4, padx=4, pady=7)
        self.grid_scroll.to_top()

    def pick_item(self, name, price):
        if isinstance(price, dict):
            self.show_sizes(name, price)
        else:
            self.add_to_order(name, price)

    # ---------------- Size chooser (grills) ----------------
    def show_sizes(self, name, sizes):
        self.hide_sheet()
        sheet = Panel(self.left_body, width=440, height=210, radius=14, pad=8,
                      shadow=True)
        self.sheet = sheet
        b = sheet.body
        tk.Label(b, text="Choose a size", font=F["h2"], bg=WHITE, fg=DARK).pack(
            pady=(16, 0))
        tk.Label(b, text=name, font=F["small"], bg=WHITE, fg=MUTED).pack(pady=(2, 12))
        row = tk.Frame(b, bg=WHITE)
        row.pack()
        for size, price in sizes.items():
            btn = RoundButton(row, "", lambda s=size, p=price: self.add_size(name, s, p),
                              118, 62, radius=10, fill=GRAY, hover="#ffedd5")
            btn.create_text(59, 22, text=size, fill=TEXT, font=F["body_b"])
            btn.create_text(59, 42, text=f"₹{price}", fill=PRICE, font=F["price"])
            btn.pack(side="left", padx=5)
        cancel = tk.Label(b, text="Cancel", font=F["small"], bg=WHITE, fg=MUTED,
                          cursor="hand2")
        cancel.pack(pady=(12, 0))
        cancel.bind("<Button-1>", lambda e: self.hide_sheet())
        sheet.place(relx=0.5, rely=0.5, anchor="center")
        tk.Misc.lift(sheet)  # Canvas.lift is tag_raise, so use the widget-level one

    def add_size(self, name, size, price):
        self.hide_sheet()
        self.add_to_order(f"{name} ({size})", price)

    def hide_sheet(self):
        if self.sheet is not None:
            self.sheet.destroy()
            self.sheet = None

    # ---------------- Order logic ----------------
    def add_to_order(self, name, price):
        if name in self.order:
            self.order[name][1] += 1
        else:
            self.order[name] = [price, 1]
        self.refresh_order()

    def change_qty(self, name, delta):
        if name not in self.order:
            return
        self.order[name][1] += delta
        if self.order[name][1] <= 0:
            del self.order[name]
        self.refresh_order()

    def remove_item(self, name):
        self.order.pop(name, None)
        self.refresh_order()

    def clear_order(self):
        self.order.clear()
        self.refresh_order()

    def new_order(self):
        if self.order:
            self.order_no += 1
        self.order.clear()
        self.table_box.var.set("")
        self.refresh_order()

    def totals(self):
        subtotal = sum(p * q for p, q in self.order.values())
        gst = subtotal * GST_RATE
        return subtotal, gst, subtotal + gst

    def refresh_order(self):
        host = self.order_scroll.inner
        for w in host.winfo_children():
            w.destroy()
        self.order_title.config(text=f"Order #{self.order_no}")

        if not self.order:
            tk.Label(host, text="No items yet.\nTap a dish to add it.", font=F["body"],
                     bg=WHITE, fg=MUTED, justify="center").pack(fill="x", pady=(60, 0))
        for name, (price, qty) in self.order.items():
            card = Panel(host, height=96, radius=10, pad=5, fill=ROW_BG)
            card.pack(fill="x", pady=(0, 10))
            b = card.body
            tk.Label(b, text=name, font=F["body_b"], bg=ROW_BG, fg=DARK,
                     anchor="w", wraplength=250, justify="left").place(x=10, y=6)
            tk.Label(b, text=f"{money(price)} × {qty} = {money(price * qty)}",
                     font=F["small"], bg=ROW_BG, fg=PRICE).place(x=10, y=30)
            step = tk.Frame(b, bg=ROW_BG)
            step.place(x=10, y=54)
            CircleButton(step, 24, GRAY_HOVER, "#d1d5db",
                         lambda n=name: self.change_qty(n, -1), "minus", TEXT).pack(side="left")
            tk.Label(step, text=str(qty), width=3, font=F["body_b"], bg=ROW_BG,
                     fg=DARK).pack(side="left")
            CircleButton(step, 24, ORANGE, ORANGE_HOVER,
                         lambda n=name: self.change_qty(n, 1), "plus", "white").pack(side="left")
            CircleButton(b, 28, RED_SOFT, "#fecaca",
                         lambda n=name: self.remove_item(n), "trash", RED).place(
                relx=1.0, x=-6, y=4, anchor="ne")

        sub, gst, total = self.totals()
        self.sub_val.config(text=money(sub))
        self.gst_val.config(text=money(gst))
        self.total_val.config(text=money(total))
        self.order_scroll.to_top() if not self.order else None

    # ---------------- Bill ----------------
    def show_bill(self):
        if not self.order:
            messagebox.showinfo("Bill", "Add at least one item to generate a bill.")
            return

        self.bill_no += 1
        now = datetime.now().strftime("%d %b %Y, %I:%M %p")
        W = 46
        table = self.table_box.var.get().strip()
        dining_line = self.dining + (f"  |  Table {table}" if self.dining == "Dine In" and table else "")

        lines = [RESTAURANT_NAME.upper().center(W),
                 "Thank you for dining with us".center(W),
                 "-" * W,
                 f"Bill No: {self.bill_no:04d}".ljust(W - len(now)) + now,
                 dining_line.ljust(W),
                 "-" * W,
                 f"{'Item':<24}{'Qty':>4}{'Rate':>8}{'Amount':>10}",
                 "-" * W]
        subtotal = 0
        for name, (price, qty) in self.order.items():
            amount = price * qty
            subtotal += amount
            parts = textwrap.wrap(name, 24) or [name]
            lines.append(f"{parts[0]:<24}{qty:>4}{price:>8,}{amount:>10,.2f}")
            lines.extend(parts[1:])
        gst = subtotal * GST_RATE
        lines += ["-" * W,
                  f"{'Subtotal':<30}{subtotal:>16,.2f}",
                  f"{'GST (5%)':<30}{gst:>16,.2f}",
                  "=" * W,
                  f"{'GRAND TOTAL':<30}{subtotal + gst:>16,.2f}",
                  "=" * W,
                  "Amounts in Indian Rupees".center(W),
                  "Visit again!".center(W)]

        win = tk.Toplevel(self.root)
        win.title(f"Bill #{self.bill_no:04d}")
        win.configure(bg=PAGE)
        win.resizable(False, False)

        paper = tk.Frame(win, bg=WHITE, highlightthickness=1, highlightbackground=BORDER)
        paper.pack(padx=28, pady=(28, 14))
        txt = tk.Text(paper, width=W, height=len(lines), font=F["mono"], bg=WHITE,
                      fg=TEXT, relief="flat", bd=0, highlightthickness=0,
                      padx=22, pady=20, wrap="none", cursor="arrow")
        txt.pack()
        txt.insert("1.0", "\n".join(lines))
        txt.tag_configure("bold", font=F["mono_b"])
        txt.tag_add("bold", "1.0", "1.end")
        grand = len(lines) - 3
        txt.tag_add("bold", f"{grand}.0", f"{grand}.end")
        txt.config(state="disabled")

        row = tk.Frame(win, bg=PAGE)
        row.pack(pady=(0, 24))
        RoundButton(row, "Close", win.destroy, 150, 44, fill=WHITE, hover=GRAY,
                    fg=TEXT, outline=BORDER).pack(side="left", padx=6)
        RoundButton(row, "New Order", lambda: (self.new_order(), win.destroy()),
                    150, 44, fill=ORANGE, hover=ORANGE_HOVER, fg="white").pack(
            side="left", padx=6)


if __name__ == "__main__":
    root = tk.Tk()
    RestaurantApp(root)
    root.mainloop()