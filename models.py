

import datetime
import json


class Customer:
    # Added 'id' to the self assignments
    def __init__(self, id, first_name, last_name, phone, street, city, state, zip_code, email, last_visit_date, highlights):
        self.id = id  # <--- DON'T FORGET THIS LINE!
        self.first_name = first_name 
        self.last_name = last_name 
        self.phone = phone
        self.street = street
        self.city = city 
        self.state = state 
        self.zip_code = zip_code
        self.email = email 
        self.last_visit_date = last_visit_date 
        self.highlights = highlights

    def log_interaction(self, note):
        self.interaction_history.append(note)



                  
        
        
class InventoryObject:
    def __init__(self, id, vendor, name, attribute, cost, price, size, count, sku):
        self.id = id
        self.vendor = vendor
        self.name = name
        self.attribute = attribute if attribute else "Standard" # Fixes "None"
        self.cost = cost
        self.price = price
        self.size = size
        self.count = count
        self.sku = sku
        
        # Calculate Margin for display (Optional)
        try:
            self.margin = (price - cost) / price
        except:
            self.margin = 0.0

    # def get_gp(self):
    #     if self.price == 0: return "0%"
    #     gp = (self.price - self.cost) / self.price
    #     return f"{gp * 100:.0f}%"

    def get_gp(self):
        """Returns the True GP: (Price - (Cost + Spiff)) / Price"""
        if self.price == 0: 
            return 0.0
        # Incorporate the spiff into the cost
        true_cost = self.cost + self.get_spiff()
        return (self.price - true_cost) / self.price

    def get_gp_display(self):
        """Converts the float to a string percentage"""
        return f"{self.get_gp() * 100:.1f}%"
    
    def get_spiff(self):
        """Looks up the spiff from the JSON file based on the mattress name."""
        try:
            with open('/app/data/spiffs.json', 'r') as f:
                spiff_data = json.load(f)
            # Use .get() to return 0.00 if the mattress name isn't found
            return float(spiff_data.get(self.name, 0.00))
        except (FileNotFoundError, json.JSONDecodeError):
            return 0.00
    
    def __repr__(self):
        # Shows up clearly in your Docker terminal
        return f"Mattress(Name: {self.name}, GP: {self.get_gp()*100:.0f}%)"

class Employee:
          
    def __init__(self, name, role, pay_type='salary', rate=0.0, emp_id=None):
        self.emp_id = emp_id
        self.name = name
        self.role = role # 'Sales' or 'Delivery'
        self.pay_type = pay_type
        self.rate = float(rate) # Hourly rate for delivery, base for sales
        self.clock_in_time = None
        self.total_hours = 0.0

    def clock_in(self, time_obj):
        self.clock_in_time = time_obj
        print(f"{self.name} clocked in.")

    def clock_out(self, time_obj):
        if self.clock_in_time:
            # Simple duration calculation (in hours)
            duration = (time_obj - self.clock_in_time).total_seconds() / 3600
            self.total_hours += duration
            self.clock_in_time = None
            print(f"{self.name} worked {duration:.2f} hours.")

    def __repr__(self):
        return f"Employee({self.name}, Role: {self.role}, Rate: ${self.rate}/hr)"
    



class Sale:
    def __init__(self, ticket_no, emp_name, base_price, spiff, tax_rate, pay_type, fees_dict, mattress_cost, delivery_fee=0.0, down_payment=0.0):
        self.ticket_no = ticket_no
        self.emp_name = emp_name
        self.base_price = float(base_price)
        self.spiff = float(spiff)
        self.tax_rate = float(tax_rate)
        self.pay_type = pay_type
        self.down_payment = float(down_payment)
        self.delivery_fee = float(delivery_fee) # Kept separate from GP calculation
        self.date = datetime.datetime.now()

        # 1. Banking / Finance Fee Calculation
        # Look up the fee (e.g., 0.0225) based on pay_type (e.g., 'credit_card')
        self.fee_rate = float(fees_dict.get(pay_type.lower(), 0.0))
        self.bank_fee_amt = self.base_price * self.fee_rate

        # 2. Adjusted Cost & Profit Logic
        # Per your Excel sheet, Bank Fees are added to the Mattress Cost
        self.adjusted_cost = float(mattress_cost) + self.bank_fee_amt
        self.profit = self.base_price - self.adjusted_cost
        
        # 3. GP Margin Formula: (Retail - Adjusted Cost) / Retail
        self.gp_margin = (self.profit / self.base_price) if self.base_price > 0 else 0

    def get_tax_amount(self):
        return self.base_price * self.tax_rate

    def get_total(self):
        # Grand total includes the delivery fee and tax
        return self.base_price + self.get_tax_amount() + self.delivery_fee

    def get_balance_due(self):
        return self.get_total() - self.down_payment
    
    

    