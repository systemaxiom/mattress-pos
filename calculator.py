import ttkbootstrap as tb
from tkinter import ttk
import tkinter

class CalculatorFrame(tb.Frame): 
    def __init__(self, parent, target_neg=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.target_neg = target_neg
        self.expression = ""
        self.display_var = tkinter.StringVar(value="0")
        
        # Display
        display = ttk.Entry(self, textvariable=self.display_var, font='TkFixedFont 18', justify='right')
        display.grid(row=0, column=0, columnspan=4, sticky='ew', pady=5, padx=5)

       
        button_matrix = [
            ('C', 'CE', '%', '/'),
            (7, 8, 9, '*'),
            (4, 5, 6, '-'),
            (1, 2, 3, '+'),
            ('±', 0, '.', '=')
        ]

        for i, row in enumerate(button_matrix):
            for j, lbl in enumerate(row):
                style = 'primary.TButton' if isinstance(lbl, int) else 'secondary.TButton'
                if lbl == '=': style = 'success.TButton'
                
                cmd = self.calculate if lbl == '=' else lambda x=lbl: self.on_click(x)
                btn = ttk.Button(self, text=lbl, style=style, command=cmd, width=5)
                btn.grid(row=i+1, column=j, sticky='nsew', padx=2, pady=2)

        
        tb.Button(self, text="📥 APPLY TO PRICE", bootstyle="warning", 
                  command=self.push_to_negotiator).grid(row=6, column=0, columnspan=4, sticky='ew', pady=10)

        for i in range(7): self.grid_rowconfigure(i, weight=1)
        for j in range(4): self.grid_columnconfigure(j, weight=1)

    def on_click(self, char):
        
        if self.expression == "0":
            self.expression = ""
            
        if char == 'C': 
            self.expression = ""
        elif char == 'CE': 
            self.expression = self.expression[:-1]
        elif char == '±':
            if self.expression.startswith('-'): 
                self.expression = self.expression[1:]
            else: 
                self.expression = '-' + self.expression
        else: 
            
            self.expression += str(char)
            
        self.display_var.set(self.expression or "0")

    def calculate(self):
        try:
            
            clean_expression = self.expression.replace('%', '/100')
            result = eval(clean_expression)
            formatted_result = f"{result:g}" 
            self.display_var.set(formatted_result)
            self.expression = formatted_result 
        except Exception as e:
            self.display_var.set("Error")
            self.expression = ""

    def push_to_negotiator(self):
        """Sends the calculator result to the Negotiator's manual price entry."""
        val = self.display_var.get()
        if self.target_neg and hasattr(self.target_neg, 'manual_price_entry'):
            self.target_neg.manual_price_entry.delete(0, 'end')
            self.target_neg.manual_price_entry.insert(0, val)