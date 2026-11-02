# Restaurant Menu & Billing System (GUI using tkinter)
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


class RestaurantApp:
    def __init__(self, root):
        self.root = root
        root.title("Restaurant Billing System")
        root.geometry("1000x560")

        self.order = {}            # item name -> [price, qty]
        self.current_category = None
        self.current_items = []    # list of (name, price or dict)
        self.size_var = tk.StringVar(value="Half")

        self.build_ui()

    # ---------------- UI ----------------
    def build_ui(self):
        # Column 1: categories
        f1 = ttk.LabelFrame(self.root, text="1. Category")
        f1.grid(row=0, column=0, padx=8, pady=8, sticky="ns")
        self.cat_list = tk.Listbox(f1, width=18, height=15, font=("Arial", 12),
                                   exportselection=False)
        self.cat_list.pack(padx=5, pady=5)
        for cat in menu:
            self.cat_list.insert(tk.END, cat)
        self.cat_list.bind("<<ListboxSelect>>", self.on_category)

        # Column 2: items + size + qty
        f2 = ttk.LabelFrame(self.root, text="2. Select Item")
        f2.grid(row=0, column=1, padx=8, pady=8, sticky="ns")
        self.item_list = tk.Listbox(f2, width=45, height=12, font=("Arial", 11),
                                    exportselection=False)
        self.item_list.pack(padx=5, pady=5)
        self.item_list.bind("<<ListboxSelect>>", self.on_item)

        self.size_frame = ttk.LabelFrame(f2, text="Size (grills only)")
        self.size_frame.pack(fill="x", padx=5, pady=3)
        self.size_buttons = {}
        for size in ("Quarter", "Half", "Full"):
            rb = ttk.Radiobutton(self.size_frame, text=size, value=size,
                                 variable=self.size_var, state="disabled")
            rb.pack(side="left", padx=8, pady=3)
            self.size_buttons[size] = rb

        qty_frame = ttk.Frame(f2)
        qty_frame.pack(pady=5)
        ttk.Label(qty_frame, text="Quantity:").pack(side="left")
        self.qty_spin = ttk.Spinbox(qty_frame, from_=1, to=50, width=5)
        self.qty_spin.set(1)
        self.qty_spin.pack(side="left", padx=5)
        ttk.Button(qty_frame, text="Add to Order",
                   command=self.add_item).pack(side="left", padx=10)

        # Column 3: order table
        f3 = ttk.LabelFrame(self.root, text="3. Your Order")
        f3.grid(row=0, column=2, padx=8, pady=8, sticky="ns")
        cols = ("Item", "Qty", "Price", "Total")
        self.tree = ttk.Treeview(f3, columns=cols, show="headings", height=13)
        widths = (190, 40, 60, 70)
        for c, w in zip(cols, widths):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="center" if c != "Item" else "w")
        self.tree.pack(padx=5, pady=5)

        self.total_label = ttk.Label(f3, text="Subtotal: Rs.0", font=("Arial", 11, "bold"))
        self.total_label.pack(pady=2)

        btns = ttk.Frame(f3)
        btns.pack(pady=5)
        ttk.Button(btns, text="Remove Selected",
                   command=self.remove_item).pack(side="left", padx=3)
        ttk.Button(btns, text="Clear All",
                   command=self.clear_order).pack(side="left", padx=3)
        ttk.Button(btns, text="Get Bill",
                   command=self.show_bill).pack(side="left", padx=3)

    # ---------------- Events ----------------
    def on_category(self, event=None):
        sel = self.cat_list.curselection()
        if not sel:
            return
        self.current_category = self.cat_list.get(sel[0])
        self.current_items = list(menu[self.current_category].items())
        self.item_list.delete(0, tk.END)
        for name, price in self.current_items:
            if isinstance(price, dict):
                sizes = "  ".join(f"{s[0]}:{p}" for s, p in price.items())
                self.item_list.insert(tk.END, f"{name}  ({sizes})")
            else:
                self.item_list.insert(tk.END, f"{name}  -  Rs.{price}")
        self.set_size_state(False)

    def on_item(self, event=None):
        sel = self.item_list.curselection()
        if not sel:
            return
        _, price = self.current_items[sel[0]]
        self.set_size_state(isinstance(price, dict))

    def set_size_state(self, enabled):
        for rb in self.size_buttons.values():
            rb.config(state="normal" if enabled else "disabled")

    def add_item(self):
        sel = self.item_list.curselection()
        if not sel:
            messagebox.showwarning("Select item", "Please select an item first.")
            return
        try:
            qty = int(self.qty_spin.get())
            if qty < 1:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Quantity", "Enter a valid quantity (1 or more).")
            return

        name, price = self.current_items[sel[0]]
        if isinstance(price, dict):
            size = self.size_var.get()
            price = price[size]
            name = f"{name} ({size})"

        if name in self.order:
            self.order[name][1] += qty
        else:
            self.order[name] = [price, qty]
        self.qty_spin.set(1)
        self.refresh_order()

    def remove_item(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Remove", "Select an item in the order list.")
            return
        for iid in sel:
            self.order.pop(iid, None)
        self.refresh_order()

    def clear_order(self):
        self.order.clear()
        self.refresh_order()

    def refresh_order(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        subtotal = 0
        for name, (price, qty) in self.order.items():
            amount = price * qty
            subtotal += amount
            self.tree.insert("", tk.END, iid=name, values=(name, qty, price, amount))
        self.total_label.config(text=f"Subtotal: Rs.{subtotal}")

    # ---------------- Bill ----------------
    def show_bill(self):
        if not self.order:
            messagebox.showinfo("Bill", "No items ordered yet.")
            return

        win = tk.Toplevel(self.root)
        win.title("Final Bill")
        txt = tk.Text(win, width=58, height=22, font=("Courier New", 10))
        txt.pack(padx=10, pady=10)

        line = "=" * 54
        out = [line, "FINAL BILL".center(54), line,
               f"{'Item':<30}{'Qty':>4}{'Price':>8}{'Total':>12}", "-" * 54]
        subtotal = 0
        for name, (price, qty) in self.order.items():
            amount = price * qty
            subtotal += amount
            out.append(f"{name:<30}{qty:>4}{price:>8}{amount:>12}")
        gst = subtotal * GST_RATE
        out += ["-" * 54,
                f"{'Subtotal':<42}{subtotal:>12.2f}",
                f"{'GST (5%)':<42}{gst:>12.2f}",
                f"{'GRAND TOTAL':<42}{subtotal + gst:>12.2f}",
                line, "Thank you! Visit again :)".center(54)]
        txt.insert(tk.END, "\n".join(out))
        txt.config(state="disabled")


root = tk.Tk()
RestaurantApp(root)
root.mainloop()