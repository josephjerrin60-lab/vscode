# Restaurant Menu & Billing System (console based)

# Normal items -> price (int)
# Grill items  -> {size: price} (dictionary), so user can choose Quarter/Half/Full
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
        "Normal Alfaham":      {"Quarter": 120, "Half": 230, "Full": 440},
        "Peri Peri Alfaham":   {"Quarter": 140, "Half": 270, "Full": 520},
        "Honey Chilli Alfaham": {"Quarter": 150, "Half": 290, "Full": 550},
        "Afghani Alfaham":     {"Quarter": 160, "Half": 310, "Full": 590},
        "Normal BBQ":          {"Quarter": 110, "Half": 210, "Full": 400},
        "Peri Peri BBQ":       {"Quarter": 130, "Half": 250, "Full": 480},
        "Arabic BBQ":          {"Quarter": 140, "Half": 270, "Full": 520},
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

order = {}  # item name -> [price, quantity]


def show_categories():
    print("\n===== MENU CATEGORIES =====")
    categories = list(menu.keys())
    for i, cat in enumerate(categories, start=1):
        print(f"{i}. {cat}")
    print("0. Finish & Get Bill")
    return categories


def show_items(category):
    print(f"\n----- {category} -----")
    items = list(menu[category].items())
    for i, (name, price) in enumerate(items, start=1):
        if isinstance(price, dict):  # grill item with sizes
            sizes = " | ".join(f"{s} Rs.{p}" for s, p in price.items())
            print(f"{i}. {name:<22} {sizes}")
        else:
            print(f"{i}. {name:<30} Rs.{price}")
    print("0. Back to categories")
    return items


def get_number(prompt):
    """Keep asking until the user enters a valid whole number."""
    while True:
        value = input(prompt).strip()
        if value.isdigit():
            return int(value)
        print("Please enter a valid number.")


def choose_size(name, sizes):
    """Ask Quarter/Half/Full. Returns (size, price) or None if cancelled."""
    size_list = list(sizes.items())
    print(f"\nSelect size for {name}:")
    for i, (size, price) in enumerate(size_list, start=1):
        print(f"{i}. {size:<8} Rs.{price}")
    print("0. Cancel")
    while True:
        s = get_number("Enter size number: ")
        if s == 0:
            return None
        if 1 <= s <= len(size_list):
            return size_list[s - 1]
        print("Invalid size, try again.")


def print_bill():
    print("\n" + "=" * 56)
    print("                      FINAL BILL")
    print("=" * 56)

    if not order:
        print("No items ordered.")
        print("=" * 56)
        return

    print(f"{'Item':<32}{'Qty':>4}{'Price':>8}{'Total':>12}")
    print("-" * 56)

    subtotal = 0
    for name, (price, qty) in order.items():
        amount = price * qty
        subtotal += amount
        print(f"{name:<32}{qty:>4}{price:>8}{amount:>12}")

    gst = subtotal * GST_RATE
    grand_total = subtotal + gst

    print("-" * 56)
    print(f"{'Subtotal':<44}{subtotal:>12.2f}")
    print(f"{'GST (5%)':<44}{gst:>12.2f}")
    print(f"{'GRAND TOTAL':<44}{grand_total:>12.2f}")
    print("=" * 56)
    print("Thank you! Visit again :)")


def main():
    print("Welcome to our Restaurant!")

    while True:
        categories = show_categories()
        choice = get_number("What would you like? Enter category number: ")

        if choice == 0:
            break
        if choice < 1 or choice > len(categories):
            print("Invalid choice, try again.")
            continue

        category = categories[choice - 1]

        # Stay inside this category until user goes back
        while True:
            items = show_items(category)
            item_choice = get_number("Select item number: ")

            if item_choice == 0:
                break
            if item_choice < 1 or item_choice > len(items):
                print("Invalid item, try again.")
                continue

            name, price = items[item_choice - 1]

            # If item has sizes (grills), ask for size first
            if isinstance(price, dict):
                result = choose_size(name, price)
                if result is None:
                    continue
                size, price = result
                name = f"{name} ({size})"

            qty = get_number(f"How many {name}? ")
            if qty == 0:
                print("Quantity can't be zero.")
                continue

            if name in order:
                order[name][1] += qty
            else:
                order[name] = [price, qty]
            print(f"Added {qty} x {name}")

    print_bill()


main()