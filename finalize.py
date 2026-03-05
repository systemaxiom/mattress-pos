

import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox, simpledialog
from datetime import datetime

import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox, simpledialog
from datetime import datetime

class FinalizeCommandCenter(tb.Toplevel):
    
    def __init__(self, parent, cart, db_helper, spiff_data, roster, customer_name, on_success_callback, store_name="ANNISTON_STORE_1"):
      
        super().__init__(title=f"Axiom | Finalize Transaction - {store_name}", size=(900, 800))
        
        self.parent = parent
        self.cart = cart
        self.store_name = store_name 
        
       
        self.raw_fees = roster.get('fees', {})
        self.roster_list = list(self.raw_fees.keys()) if self.raw_fees else ["CASH", "CREDIT"]
        
        
        self.staff_list = roster.get('associates', [])
        self.staff_names = [s.get('name', 'Unknown') for s in self.staff_list] if self.staff_list else ["Default"]

        # Default Tax Options
        self.tax_options = {"Standard (9%)": 9.0, "Tax Exempt": 0.0}
        
        self.db = db_helper
        self.spiffs = spiff_data
        self.customer_name = customer_name
        self.on_success = on_success_callback
        
        self.setup_ui()
        self.update_math() 
    
    def setup_ui(self):
        self.item_salesmen_vars = [] 
        
        self.container = tb.Frame(self, padding=20)
        self.container.pack(fill='both', expand=True)

        # --- RIGHT: THE COMMAND PANEL ---
        self.right_side = tb.Frame(self.container, width=350, bootstyle='secondary', padding=20)
        self.right_side.pack(side='right', fill='y')
        self.right_side.pack_propagate(False)

        self.delivery_var = tb.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.delivery_ent = tb.Entry(self.right_side, textvariable=self.delivery_var)
        self.delivery_ent.pack(fill='x', pady=5)
        
        tb.Label(self.right_side, text="TICKET MARGIN", font=("Helvetica", 10, "bold"), bootstyle='inverse-secondary').pack()
        self.gp_label = tb.Label(self.right_side, text="0.0%", font=("Helvetica", 32, "bold"), bootstyle='inverse-secondary')
        self.gp_label.pack(pady=10)
        tb.Label(self.right_side, text="Primary Associate", bootstyle='inverse-secondary').pack(anchor='w', pady=(10, 0))
        self.salesman_cb = tb.Combobox(self.right_side, values=self.staff_names, state="readonly")
       
        def sync_salesmen(event=None):
            primary = self.salesman_cb.get()
            for var in self.item_salesmen_vars:
                var.set(primary)

        self.salesman_cb.bind("<<ComboboxSelected>>", sync_salesmen)
        
        if self.staff_names: 
            self.salesman_cb.current(0)
           
            
        self.salesman_cb.pack(fill='x', pady=5)

        tb.Label(self.right_side, text="Payment Method", bootstyle='inverse-secondary').pack(anchor='w', pady=(10, 0))
        self.method_cb = tb.Combobox(self.right_side, values=self.roster_list, state="readonly")
        if self.roster_list: self.method_cb.current(0)
        self.method_cb.pack(fill='x', pady=5)
        self.method_cb.bind("<<ComboboxSelected>>", self.update_math)

        tb.Label(self.right_side, text="Tax Rate", bootstyle='inverse-secondary').pack(anchor='w', pady=(10, 0))
        self.tax_cb = tb.Combobox(self.right_side, values=list(self.tax_options.keys()), state="readonly")
        self.tax_cb.current(0)
        self.tax_cb.pack(fill='x', pady=5)
        self.tax_cb.bind("<<ComboboxSelected>>", self.update_math)

        tb.Label(self.right_side, text="Down Payment ($)", bootstyle='inverse-secondary').pack(anchor='w', pady=(10, 0))
        self.dp_var = tb.StringVar(value="0.00")
        self.dp_ent = tb.Entry(self.right_side, textvariable=self.dp_var, justify='right')
        self.dp_ent.pack(fill='x', pady=5)
        self.dp_var.trace_add("write", self.update_math)

        self.summary = tb.Frame(self.right_side, bootstyle='secondary')
        self.summary.pack(fill='x', side='bottom', pady=(10, 0))

        self.sub_lbl = tb.Label(self.summary, text="Subtotal: $0.00", bootstyle='inverse-secondary')
        self.sub_lbl.pack(anchor='e')
        
        self.tax_lbl = tb.Label(self.summary, text="Tax: $0.00", bootstyle='inverse-secondary')
        self.tax_lbl.pack(anchor='e')

        self.total_lbl = tb.Label(self.summary, text="Grand Total: $0.00", font=("Helvetica", 18, "bold"), bootstyle='success')
        self.total_lbl.pack(anchor='e', pady=10)
        
        self.balance_lbl = tb.Label(self.summary, text="Balance Due: $0.00", font=("Helvetica", 14, "bold"), bootstyle='warning')
        self.balance_lbl.pack(anchor='e', pady=5)

        tb.Button(self.summary, text="COMPLETE SALE", bootstyle='success', command=self.execute_final_save).pack(fill='x', pady=10)

        # --- LEFT: ITEM LIST (SCROLLABLE CANVAS) ---
        self.left_side = tb.Frame(self.container)
        self.left_side.pack(side='left', fill='both', expand=True, padx=(0, 20))

        tb.Label(self.left_side, text="LINE ITEMS", font=("Helvetica", 12, "bold")).pack(anchor='w', pady=(0, 10))

        self.canvas = tb.Canvas(self.left_side, highlightthickness=0)
        self.scrollbar = tb.Scrollbar(self.left_side, orient="vertical", command=self.canvas.yview)
        
        self.item_scroll = tb.Frame(self.canvas)
        self.item_scroll.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_window = self.canvas.create_window((0, 0), window=self.item_scroll, anchor="nw")
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        
        self.price_entries = []
        for item in self.cart:
            row = tb.Frame(self.item_scroll, padding=10)
            row.pack(fill='x', pady=2)
            
            tb.Label(row, text=f"{item['vendor']} {item['name']} ({item['size']})", width=35).pack(side='left')
            
            s_var = tb.StringVar()
            s_cb = tb.Combobox(row, textvariable=s_var, values=self.staff_names, state="readonly", width=12)
            s_cb.pack(side='left', padx=10)
            self.item_salesmen_vars.append(s_var)
            
            p_var = tb.StringVar(value=str(item['price']))
            ent = tb.Entry(row, textvariable=p_var, width=12, justify='right')
            ent.pack(side='right')
            
            p_var.trace_add("write", self.update_math)
            self.price_entries.append((item, p_var))

        # 2. CALL THE SYNC AT THE VERY END OF setup_ui
        sync_salesmen()


    def update_math(self, *args):
        try:
            total_revenue = sum(float(var.get() or 0) for _, var in self.price_entries)
            
            tax_rate_percent = self.tax_options.get(self.tax_cb.get(), 0.0) 
            tax_amt = total_revenue * (tax_rate_percent / 100)
            
            self.grand_total = total_revenue + tax_amt

            try:
                down_payment = float(self.dp_var.get() or 0)
            except ValueError:
                down_payment = 0.0
            
            balance_due = self.grand_total - down_payment

            self.sub_lbl.config(text=f"Subtotal: ${total_revenue:,.2f}")
            self.tax_lbl.config(text=f"Tax ({tax_rate_percent}%): ${tax_amt:,.2f}")
            self.total_lbl.config(text=f"Grand Total: ${self.grand_total:,.2f}")
            
            if hasattr(self, 'balance_lbl'):
                if balance_due > 0.01:
                    self.balance_lbl.config(text=f"Balance Due: ${balance_due:,.2f}", bootstyle='danger')
                elif balance_due < -0.01:
                    self.balance_lbl.config(text=f"Change Due: ${abs(balance_due):,.2f}", bootstyle='warning')
                else:
                    self.balance_lbl.config(text="PAID IN FULL", bootstyle='success')

            # --- GP CALCULATION ---
            total_cost = 0
            total_fees = 0
            method = self.method_cb.get()
            fee_rate = self.raw_fees.get(method, 0.0)
            
            for item, var in self.price_entries:
                p = float(var.get() or 0)
                total_cost += float(item.get('cost', 0))
                total_fees += p * fee_rate
                
            profit = total_revenue - total_cost - total_fees
            gp = (profit / total_revenue * 100) if total_revenue > 0 else 0
            self.gp_label.config(text=f"{gp:.1f}%")
            self.gp_label.config(bootstyle='success-inverse' if gp >= 40 else 'danger-inverse')
                
        except Exception as e:
            pass 

    def process_split_payments(self):
        """Smart payment logic that bypasses popups if paying in full."""
        self.all_payments = []
        main_method = self.method_cb.get()
        
        try:
            down_payment = float(self.dp_var.get() or 0)
        except ValueError:
            down_payment = 0.0

        
        if down_payment <= 0.01 or down_payment >= (self.grand_total - 0.01):
            self.all_payments.append({'amount': self.grand_total, 'method': main_method})
            return True

       
        self.all_payments.append({'amount': down_payment, 'method': main_method})
        remaining_balance = self.grand_total - down_payment

        valid_methods_str = ", ".join(self.roster_list)

        while remaining_balance > 0.01:
            prompt = f"Total Due: ${self.grand_total:,.2f}\nRemaining: ${remaining_balance:,.2f}\n\nEnter Amount for next payment:"
            amount = simpledialog.askfloat("Split Payment", prompt, parent=self)
            
            if amount is None or amount <= 0:
                if messagebox.askyesno("Cancel?", "Stop payment collection? (Progress will be lost)", parent=self):
                    return False
                continue

            # Call our custom dropdown dialog
            method_popup = PaymentMethodDialog(self, self.roster_list)
            method = method_popup.result
            
            # If they somehow closed the window without picking, default to OTHER
            if not method: 
                method = "OTHER"

            self.all_payments.append({'amount': amount, 'method': method.upper()})
            remaining_balance -= amount

        messagebox.showinfo("Paid", "Balance settled. Finalizing ticket...", parent=self)
        return True

    def execute_final_save(self):
        try:
            if not self.process_split_payments():
                return 

            ticket_no = f"TICK-{datetime.now().strftime('%m%d%y%H%M')}"
            
            raw_subtotal = sum(float(var.get() or 0) for _, var in self.price_entries)
            tax_rate_val = self.tax_options.get(self.tax_cb.get(), 0.0) / 100
            tax_amt = raw_subtotal * tax_rate_val
            
            totals = {'sub': raw_subtotal, 'tax': tax_amt, 'final': self.grand_total}
            methods_str = ", ".join([p['method'] for p in self.all_payments])

            for i, item in enumerate(self.cart):
                full_item_name = f"{item['vendor']} {item['name']} ({item['size']})"
                
                # Get the specific salesman for THIS item line!
                item_salesman = self.item_salesmen_vars[i].get()
                
                fee_rate = self.raw_fees.get(self.method_cb.get(), 0.0)
                bank_fee_amt = item['price'] * fee_rate
                spiff_val = self.spiffs.get(item['name'], 0.00)
                profit_val = item['price'] - item['cost'] - bank_fee_amt
                gp_val = (profit_val / item['price']) if item['price'] > 0 else 0

              

                sale_data = {
                    "ticket_id": ticket_no,      
                    "sku": item.get('sku', ''),
                    "item": full_item_name,
                    "salesman": item_salesman,    
                    "price": item['price'],
                    "tax_rate": tax_rate_val,
                    "delivery_fee": 0.0,         
                    "bank_fee_amt": bank_fee_amt,
                    "profit": profit_val,
                    "gp_margin": gp_val,
                    "spiff": spiff_val,
                    "method": methods_str,       
                    "pay_method": methods_str,  
                    "down_payment": self.all_payments[0]['amount'] if self.all_payments else 0.0,
                    "traffic_count": 1,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "customer_name": self.customer_name,
                    "delivery_date": self.delivery_var.get(),
                    "status": "COMPLETED"
                }

                self.db.insert_data('sales', sale_data)

                self.db.update_table(
                    table_name='inventory',
                    data="count = count - 1",
                    where_clause="name = ? AND size = ? AND attribute = ?",
                    where_args=(item['name'], item['size'], item['attribute'])
                )

            self.parent.reporting.print_ticket(
                ticket_no, 
                self.customer_name, 
                self.cart, 
                totals, 
                self.delivery_var.get(), 
                self.salesman_cb.get()
            )

            if self.on_success:
                self.on_success()
            self.destroy()

        except Exception as e:
            messagebox.showerror("Save Error", f"Error during final save: {e}", parent=self)
            print(f"❌ Save Error: {e}") 

class PaymentMethodDialog(tb.Toplevel):
    def __init__(self, parent, options):
        super().__init__(title="Payment Method", parent=parent, size=(300, 150))
        self.result = None
        
        # Center the popup slightly
        self.position_center()

        tb.Label(self, text="Select Split Payment Method:", font=("Helvetica", 10)).pack(pady=10)
        
        self.cb = tb.Combobox(self, values=options, state="readonly", font=("Helvetica", 11))
        if options: 
            self.cb.current(0)
        self.cb.pack(fill='x', padx=20, pady=5)
        
        tb.Button(self, text="CONFIRM", bootstyle="success", command=self.confirm).pack(pady=10)
        
        # Make the window modal (blocks the app until answered)
        self.transient(parent)
        self.grab_set()
        self.wait_window(self)
        
    def confirm(self):
        self.result = self.cb.get()
        self.destroy()