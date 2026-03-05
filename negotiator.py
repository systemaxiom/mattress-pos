import ttkbootstrap as tb
from ttkbootstrap.constants import *

class NegotiatorFrame(tb.Frame): 
    def __init__(self, parent, cart, spiff_data, roster_data, on_finalize):
        super().__init__(parent)
        
        self.items = cart
        self.spiffs = spiff_data
        self.roster = roster_data
        self.on_finalize = on_finalize
        
        
        self.pay_options = list(self.roster.get('fees', {}).keys())
        if not self.pay_options:
            self.pay_options =  ['cash','credit']
        
        
        self.total_cost = sum(
            float(item.get('cost', 0)) + float(self.spiffs.get(item['name'], 0)) 
            for item in self.items
        )
        
        self.setup_ui()
        self.calculate_all()

    def setup_ui(self):
        tb.Label(self, text="Deal Summary", font=("Helvetica", 18, "bold"), bootstyle='info').pack(pady=10)
        
        # Item List
        self.item_frame = tb.Frame(self)
        self.item_frame.pack(fill='both', expand=True, padx=20)
        
        self.price_entries = []
        for item in self.items:
            row = tb.Frame(self.item_frame)
            row.pack(fill=X, pady=5)
            
            tb.Label(row, text=item['name'], width=30).pack(side='left')
            
            price_var = tb.StringVar(value=str(item['price']))
           
            self.manual_price_entry = tb.Entry(row, textvariable=price_var, width=10)
            self.manual_price_entry.pack(side='right')
            
            price_var.trace_add("write", lambda *args: self.calculate_all())
            self.price_entries.append((item, price_var))

      
        ctrl_frame = tb.Labelframe(self, text="Negotiation Tools", padding=15)
        ctrl_frame.pack(fill=X, padx=20, pady=20)

        self.target_gp_var = tb.StringVar(value="45")
        tb.Label(ctrl_frame, text="Target GP %:").grid(row=0, column=0, sticky=W)
        tb.Entry(ctrl_frame, textvariable=self.target_gp_var, width=8).grid(row=0, column=1, padx=5)
        self.target_gp_var.trace_add("write", lambda *args: self.calculate_all())

        tb.Label(ctrl_frame, text="Payment Method:").grid(row=1, column=0, sticky=W, pady=10)
        self.method_cb = tb.Combobox(ctrl_frame, values=self.pay_options, state="readonly")
        self.method_cb.current(0) 
        self.method_cb.grid(row=1, column=1, padx=5)
        self.method_cb.bind("<<ComboboxSelected>>", self.calculate_all)

        # Dashboard
        self.stats_frame = tb.Frame(self, bootstyle='secondary', padding=15)
        self.stats_frame.pack(fill=X, pady=10)
        
        self.lbl_total = tb.Label(self.stats_frame, text="Total Price: $0.00", font=("Helvetica", 12))
        self.lbl_total.pack()
        
        self.lbl_gp = tb.Label(self.stats_frame, text="Current GP: 0%", font=("Helvetica", 14, "bold"))
        self.lbl_gp.pack()

        self.lbl_needed = tb.Label(self.stats_frame, text="Price Needed: $0.00", bootstyle='warning')
        self.lbl_needed.pack()

        tb.Button(self, text="Finalize & Send to Cart", bootstyle='success', 
                  command=self.finalize).pack(pady=20)

    def calculate_all(self, *args):
        try:
            current_total = sum(float(var.get() or 0) for _, var in self.price_entries)
            
           
            pay_type = self.method_cb.get()
            fee_rate = self.roster.get('fees', {}).get(pay_type, 0.00)
            bank_fee = current_total * fee_rate
            
            actual_cost = self.total_cost + bank_fee
            gp_dollars = current_total - actual_cost
            gp_percent = (gp_dollars / current_total * 100) if current_total > 0 else 0
            
            target_pct = float(self.target_gp_var.get() or 0) / 100
            
            needed_price = self.total_cost / (1 - target_pct - fee_rate) if (1 - target_pct - fee_rate) > 0 else 0
            
            self.lbl_total.config(text=f"Total Price: ${current_total:,.2f}")
            self.lbl_gp.config(text=f"Current GP: {gp_percent:.1f}%")
            self.lbl_needed.config(text=f"Needed for {self.target_gp_var.get()}%: ${needed_price:,.2f}")
            
            boot = 'success' if gp_percent >= float(self.target_gp_var.get() or 0) else 'danger'
            self.lbl_gp.config(bootstyle=boot)
        except Exception as e:
            print(f"Calc Error: {e}")

    def finalize(self):
        for item, var in self.price_entries:
            item['price'] = float(var.get() or 0)
        self.on_finalize(self.items)
        
        self.master.master.destroy()


