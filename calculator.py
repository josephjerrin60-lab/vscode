import tkinter as tk


class Calculator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Calculator")
        self.resizable(False, False)
        self.configure(bg="#202124", padx=12, pady=12)

        self.expression = ""
        self.display_value = tk.StringVar(value="0")

        display = tk.Entry(
            self,
            textvariable=self.display_value,
            justify="right",
            font=("Arial", 28),
            state="readonly",
            readonlybackground="#ffffff",
            fg="#202124",
            width=16,
        )
        display.grid(row=0, column=0, columnspan=4, sticky="nsew", pady=(0, 10), ipady=10)

        buttons = [
            ("C", 1, 0, self.clear, "#d64b4b"),
            ("⌫", 1, 1, self.backspace, "#60646c"),
            ("÷", 1, 2, lambda: self.add_operator("/"), "#f59e0b"),
            ("×", 1, 3, lambda: self.add_operator("*"), "#f59e0b"),
            ("7", 2, 0, lambda: self.add("7"), "#3a3d42"),
            ("8", 2, 1, lambda: self.add("8"), "#3a3d42"),
            ("9", 2, 2, lambda: self.add("9"), "#3a3d42"),
            ("−", 2, 3, lambda: self.add_operator("-"), "#f59e0b"),
            ("4", 3, 0, lambda: self.add("4"), "#3a3d42"),
            ("5", 3, 1, lambda: self.add("5"), "#3a3d42"),
            ("6", 3, 2, lambda: self.add("6"), "#3a3d42"),
            ("+", 3, 3, lambda: self.add_operator("+"), "#f59e0b"),
            ("1", 4, 0, lambda: self.add("1"), "#3a3d42"),
            ("2", 4, 1, lambda: self.add("2"), "#3a3d42"),
            ("3", 4, 2, lambda: self.add("3"), "#3a3d42"),
            ("=", 4, 3, self.calculate, "#3b82f6"),
            ("0", 5, 0, lambda: self.add("0"), "#3a3d42"),
            (".", 5, 1, lambda: self.add_decimal(), "#3a3d42"),
        ]

        for label, row, column, command, color in buttons:
            span = 2 if label == "0" else 1
            button = tk.Button(
                self,
                text=label,
                command=command,
                font=("Arial", 20, "bold"),
                bg=color,
                fg="white",
                activebackground=color,
                activeforeground="white",
                relief="flat",
                width=4,
                height=2,
            )
            button.grid(row=row, column=column, columnspan=span, padx=3, pady=3, sticky="nsew")

        for column in range(4):
            self.grid_columnconfigure(column, weight=1)

        self.bind("<Return>", lambda event: self.calculate())
        self.bind("<Escape>", lambda event: self.clear())
        self.bind("<Key>", self.handle_key)

    def update_display(self):
        self.display_value.set(self.expression or "0")

    def add(self, value):
        if self.display_value.get() == "Error":
            self.expression = ""
        self.expression += value
        self.update_display()

    def add_decimal(self):
        current_number = self.expression.replace("+", " ").replace("-", " ").replace("*", " ").replace("/", " ").split()
        if not current_number or "." not in current_number[-1]:
            self.add("0." if not current_number else ".")

    def add_operator(self, operator):
        if not self.expression:
            if operator == "-":
                self.expression = "-"
        elif self.expression[-1] in "+-*/":
            self.expression = self.expression[:-1] + operator
        else:
            self.expression += operator
        self.update_display()

    def clear(self):
        self.expression = ""
        self.update_display()

    def backspace(self):
        self.expression = self.expression[:-1]
        self.update_display()

    def calculate(self):
        try:
            if not self.expression or self.expression[-1] in "+-*/":
                return
            result = eval(self.expression, {"__builtins__": {}}, {})
            self.expression = str(int(result) if isinstance(result, float) and result.is_integer() else result)
            self.update_display()
        except (ArithmeticError, SyntaxError, TypeError, ValueError):
            self.expression = ""
            self.display_value.set("Error")

    def handle_key(self, event):
        if event.char in "0123456789":
            self.add(event.char)
        elif event.char == ".":
            self.add_decimal()
        elif event.char in "+-*/":
            self.add_operator(event.char)
        elif event.keysym == "BackSpace":
            self.backspace()


if __name__ == "__main__":
    Calculator().mainloop()
