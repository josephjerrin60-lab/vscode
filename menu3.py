# Restaurant Menu & Billing System - colourful tile GUI (tkinter)
import tkinter as tk
from tkinter import ttk, messagebox

# Normal items -> price (int)
# Grill items  -> {size: price} (dictionary)
menu = {
    "Starters": {
        "Samosa": 30,
        "Chicken 65": 170,
        "French Fries": 100,
        "Paneer Tikka": 150,
    },
    "Main Course": {
        "Chicken Biriyani": 190,
        "Porotta & Beef Roast": 160,
        "Appam & Pork Fry": 180,
        "Butter Naan & Butter Chicken": 200,
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
    "Juices": {
        "Orange Juice": 60,
        "Watermelon Juice": 50,
        "Mango Shake": 80,
        "Fresh Lime Soda": 40,
    },
}

GST_RATE = 0.05  # 5% GST

# ---------- Colours (change these to restyle the whole app) ----------
BG = "#fdf6ec"        # page background (cream)
HEADER = "#2d1b14"    # header bar (dark brown)
GOLD = "#f4c542"      # title text
GREEN = "#27ae60"
RED = "#c0392b"
CAT_COLORS = {
    "Starters": "#e67e22",
    "Main Course": "#c0392b",
    "Breads": "#b7950b",
    "Grills": "#8e44ad",
    "Desserts": "#e84393",
    "Juices": "#16a085",
}


def lighten(hex_color, amount=28):
    """Return a slightly lighter shade (used for the hover effect)."""
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(min(255, c + amount) for c in (r, g, b))


def make_tile(parent, text, color, command, width=14, height=3,
              font=("Helvetica", 12, "bold"), wrap=150):
    """A clickable coloured tile. Uses Label because tk.Button ignores
    background colours on macOS."""
    tile = tk.Label(parent, text=text, bg=color, fg="white", font=font,
                    width=width, height=height, wraplength=wrap,
                    cursor="hand2", justify="center")
    tile.bind("<Button-1>", lambda e: command())
    tile.bind("<Enter>", lambda e: tile.config(bg=lighten(color)))
    tile.bind("<Leave>", lambda e: tile.config(bg=color))
    return tile


class RestaurantApp:
    def __init__(self, root):
        self.root = root
        root.title("Restaurant Billing System")
        root.geometry("1280x760")
        root.configure(bg=BG)

        self.order = {}       # item name -> [price, qty]
        self.cat_tiles = {}   # category -> tile widget
        self.current_category = None

        self.setup_styles()
        self.build_ui()
        self.select_category(list(menu)[0])

    # ---------------- Styles ----------------
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")  # 'clam' lets us colour the table on macOS
        style.configure("Treeview", background="white", fieldbackground="white",
                        rowheight=30, font=("Helvetica", 12))
        style.configure("Treeview.Heading", background=HEADER, foreground="white",
                        font=("Helvetica", 11, "bold"))
        style.map("Treeview.Heading", background=[("active", HEADER)])
        style.map("Treeview", background=[("selected", "#e67e22")],
                  foreground=[("selected", "white")])

    # ---------------- UI ----------------
    def build_ui(self):
        # Header bar
        header = tk.Frame(self.root, bg=HEADER)
        header.pack(fill="x")
        tk.Label(header, text="RESTAURANT MENU", font=("Georgia", 22, "bold"),
                 bg=HEADER, fg=GOLD).pack(side="left", padx=20, pady=12)
        tk.Label(header, text="Tap a category, then tap an item to add it",
                 font=("Helvetica", 12), bg=HEADER,
                 fg="#e8d9c5").pack(side="right", padx=20)

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=12, pady=12)

        # ----- Left: category tiles -----
        left = tk.Frame(body, bg=BG)
        left.pack(side="left", fill="y")
        tk.Label(left, text="CATEGORIES", font=("Helvetica", 11, "bold"),
                 bg=BG, fg="#7a5c45").pack(anchor="w", pady=(0, 6))
        for cat in menu:
            tile = make_tile(left, cat, CAT_COLORS[cat],
                             lambda c=cat: self.select_category(c),
                             width=16, height=2)
            tile.pack(pady=5)
            self.cat_tiles[cat] = tile

        # ----- Right: order panel -----
        right = tk.Frame(body, bg=BG)
        right.pack(side="right", fill="y", padx=(12, 0))
        tk.Label(right, text="YOUR ORDER", font=("Helvetica", 11, "bold"),
                 bg=BG, fg="#7a5c45").pack(anchor="w", pady=(0, 6))

        cols = ("Item", "Qty", "Price", "Total")
        self.tree = ttk.Treeview(right, columns=cols, show="headings", height=11)
        for c, w in zip(cols, (175, 45, 65, 75)):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="w" if c == "Item" else "center")
        self.tree.pack()

        self.subtotal_label = tk.Label(right, text="Subtotal: Rs.0",
                                       font=("Helvetica", 14, "bold"),
                                       bg=BG, fg=HEADER)
        self.subtotal_label.pack(pady=6)

        row1 = tk.Frame(right, bg=BG)
        row1.pack(pady=3)
        make_tile(row1, "+ 1", "#2980b9", lambda: self.change_qty(1),
                  width=7, height=2).pack(side="left", padx=3)
        make_tile(row1, "- 1", "#2980b9", lambda: self.change_qty(-1),
                  width=7, height=2).pack(side="left", padx=3)
        make_tile(row1, "Remove", "#7f8c8d", self.remove_item,
                  width=8, height=2).pack(side="left", padx=3)
        make_tile(row1, "Clear", "#7f8c8d", self.clear_order,
                  width=7, height=2).pack(side="left", padx=3)

        make_tile(right, "GET BILL", GREEN, self.show_bill,
                  width=38, height=2, font=("Helvetica", 14, "bold"),
                  wrap=340).pack(pady=8)

        self.status = tk.Label(right, text="", font=("Helvetica", 11, "italic"),
                               bg=BG, fg="#7a5c45")
        self.status.pack()

        # ----- Centre: item tiles + size tiles -----
        center = tk.Frame(body, bg=BG)
        center.pack(side="left", fill="both", expand=True, padx=14)

        self.cat_heading = tk.Label(center, text="", font=("Georgia", 20, "bold"),
                                    bg=BG, fg=HEADER)
        self.cat_heading.pack(anchor="w", pady=(0, 8))

        self.items_frame = tk.Frame(center, bg=BG)
        self.items_frame.pack(anchor="nw")

        self.size_frame = tk.Frame(center, bg="#f3e6d2")
        self.size_frame.pack(side="bottom", fill="x", pady=8, ipady=6)

    # ---------------- Category & items ----------------
    def select_category(self, cat):
        self.current_category = cat
        color = CAT_COLORS[cat]

        # highlight the selected category tile
        for name, tile in self.cat_tiles.items():
            tile.config(highlightthickness=5 if name == cat else 0,
                        highlightbackground=HEADER, highlightcolor=HEADER)

        self.cat_heading.config(text=cat, fg=color)
        self.clear_frame(self.items_frame)
        self.clear_frame(self.size_frame)

        for i, (name, price) in enumerate(menu[cat].items()):
            if isinstance(price, dict):
                label = f"{name}\nfrom Rs.{min(price.values())}"
            else:
                label = f"{name}\nRs.{price}"
            tile = make_tile(self.items_frame, label, color,
                             lambda n=name, p=price: self.pick_item(n, p),
                             width=19, height=4, wrap=190)
            tile.grid(row=i // 3, column=i % 3, padx=6, pady=6)

    def pick_item(self, name, price):
        if isinstance(price, dict):      # grill -> ask size
            self.show_sizes(name, price)
        else:
            self.clear_frame(self.size_frame)
            self.add_to_order(name, price)

    def show_sizes(self, name, sizes):
        self.clear_frame(self.size_frame)
        tk.Label(self.size_frame, text=f"Choose size for {name}:",
                 font=("Helvetica", 13, "bold"), bg="#f3e6d2",
                 fg=HEADER).pack(anchor="w", padx=12, pady=(8, 4))
        row = tk.Frame(self.size_frame, bg="#f3e6d2")
        row.pack(anchor="w", padx=8, pady=(0, 8))
        for size, price in sizes.items():
            make_tile(row, f"{size}\nRs.{price}", CAT_COLORS["Grills"],
                      lambda s=size, p=price: self.add_to_order(f"{name} ({s})", p),
                      width=11, height=2).pack(side="left", padx=6)

    @staticmethod
    def clear_frame(frame):
        for widget in frame.winfo_children():
            widget.destroy()

    # ---------------- Order handling ----------------
    def add_to_order(self, name, price):
        if name in self.order:
            self.order[name][1] += 1
        else:
            self.order[name] = [price, 1]
        self.refresh_order(select=[name])
        self.status.config(text=f"Added: {name}")

    def change_qty(self, delta):
        sel = list(self.tree.selection())
        if not sel:
            self.status.config(text="Select a row in the order first")
            return
        for iid in sel:
            self.order[iid][1] += delta
            if self.order[iid][1] <= 0:
                del self.order[iid]
        self.refresh_order(select=sel)

    def remove_item(self):
        sel = list(self.tree.selection())
        if not sel:
            self.status.config(text="Select a row in the order first")
            return
        for iid in sel:
            self.order.pop(iid, None)
        self.refresh_order()

    def clear_order(self):
        self.order.clear()
        self.refresh_order()
        self.status.config(text="Order cleared")

    def refresh_order(self, select=None):
        for row in self.tree.get_children():
            self.tree.delete(row)
        subtotal = 0
        for name, (price, qty) in self.order.items():
            amount = price * qty
            subtotal += amount
            self.tree.insert("", tk.END, iid=name,
                             values=(name, qty, price, amount))
        self.subtotal_label.config(text=f"Subtotal: Rs.{subtotal}")
        if select:
            keep = [s for s in select if s in self.order]
            if keep:
                self.tree.selection_set(keep)

    # ---------------- Bill ----------------
    def show_bill(self):
        if not self.order:
            messagebox.showinfo("Bill", "No items ordered yet.")
            return

        win = tk.Toplevel(self.root)
        win.title("Final Bill")
        win.configure(bg=BG)
        tk.Label(win, text="FINAL BILL", font=("Georgia", 18, "bold"),
                 bg=HEADER, fg=GOLD).pack(fill="x", ipady=8)

        txt = tk.Text(win, width=56, height=22, font=("Courier", 12),
                      bg="white", relief="flat")
        txt.pack(padx=12, pady=12)

        line = "=" * 52
        out = [f"{'Item':<28}{'Qty':>4}{'Price':>8}{'Total':>12}", "-" * 52]
        subtotal = 0
        for name, (price, qty) in self.order.items():
            amount = price * qty
            subtotal += amount
            out.append(f"{name:<28}{qty:>4}{price:>8}{amount:>12}")
        gst = subtotal * GST_RATE
        out += ["-" * 52,
                f"{'Subtotal':<40}{subtotal:>12.2f}",
                f"{'GST (5%)':<40}{gst:>12.2f}",
                line,
                f"{'GRAND TOTAL':<40}{subtotal + gst:>12.2f}",
                line, "", "Thank you! Visit again :)".center(52)]
        txt.insert(tk.END, "\n".join(out))
        txt.config(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    RestaurantApp(root)
    root.mainloop()