import os
import json
import sqlite3
from datetime import *
from tkinter import messagebox
import ttkbootstrap as tb
import calendar
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image

class ReportingEngine:
    def __init__(self, db_helper,staff_data=None):
        self.db = db_helper
        
        self.staff_data = staff_data if staff_data else {}
        # Smart Path Setup
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(base_dir, "wharehouse_data")
        
        self.paths = {
            "roster": os.path.join(self.data_dir, "roster.json"),
            "receipts": os.path.join(self.data_dir, "receipts"),
            "images": os.path.join(self.data_dir, "barcodes_2.png")
        }
        
        if not os.path.exists(self.paths["receipts"]):
            os.makedirs(self.paths["receipts"])
        
      

    
    
    
    def get_monthly_projections(self, store_id):
        # 1. Get overhead, default to 17500.00 if key is missing
        overhead = float(self.staff_data.get('overhead', {}).get(store_id, 17500.00))
    
        # 2. Get revenue
        month_str = datetime.now().strftime("%Y-%m")
        query = f"SELECT SUM(price) FROM sales WHERE date LIKE '{month_str}%'"
        res = self.db.execute_manual_query(query)
    
        # FIX: Ensure current_revenue is NEVER None
        raw_val = res[0][0] if res and res[0][0] is not None else 0.0
        current_revenue = float(raw_val)
    
        # 3. Calculate difference
        diff = current_revenue - overhead
    
        return current_revenue, overhead, diff


    def get_full_performance_data(self, store_id="Saks"):
        stats = []
        try:
            today = datetime.now()
            month_str = today.strftime("%Y-%m")
            
            # Pull overhead from our pre-loaded staff_data
            total_overhead = self.staff_data.get('overhead', {}).get(store_id, 17500.00)
            daily_req = total_overhead / 30

            # Loop through 'associates' (the new key in your roster.json)
            for associate in self.staff_data.get('associates', []):
                name = associate['name']
                
                # Check schedule from the 'employees' section of the JSON
                schedule = self.staff_data.get('employees', {}).get(name, [])
                
                days_worked_count = 0
                for d in range(1, today.day + 1):
                    day_name = datetime.date(today.year, today.month, d).strftime("%A")
                    if day_name in schedule:
                        days_worked_count += 1
                
                needs = days_worked_count * daily_req
                query = f"SELECT SUM(profit) FROM sales WHERE salesman = '{name}' AND date LIKE '{month_str}%'"
                res = self.db.execute_manual_query(query)
                made = res[0][0] if res and res[0][0] else 0.0
                
                stats.append({"name": name, "needs": needs, "made": made})
        except Exception as e:
            print(f"Performance Data Error: {e}")
            return []
        return stats
    
    def get_payroll_dates(self):
        """Calculates the current Wed-Tue pay cycle."""
        today = datetime.now().date()
        # Wednesday is index 2. This math finds the most recent Wednesday.
        offset = (today.weekday() - 2) % 7
        last_wed = today - timedelta(days=offset)
        next_tue = last_wed + timedelta(days=6)
        return last_wed, next_tue
    
    def generate_weekly_spiff_report(self):
        start, end = self.get_payroll_dates()
        
        # Query ONLY your sales across BOTH locations for this specific week
        query = """
            SELECT date, item, price, store_location 
            FROM sales 
            WHERE salesperson = 'Lindsey' 
            AND date >= ? AND date <= ?
        """
        params = (start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d 23:59"))
        
        sales_data = self.db.execute_manual_query(query, params)
        
        # Now, match the 'item' against your spiff_data JSON
        total_spiff = 0
        report_text = f"Spiff Report: {start} to {end}\n"
        report_text += "-"*30 + "\n"
        
        for sale in sales_data:
            item_name = sale[1]
            # Logic to lookup spiff value for that mattress model
            amt = self.spiff_data.get(item_name, 0) 
            total_spiff += amt
            report_text += f"{sale[0]} | {item_name} | ${amt}\n"
            
        messagebox.showinfo("Weekly Payout", f"{report_text}\nTotal Spiff: ${total_spiff:.2f}")

    def print_ticket(self, ticket_number, customer_full_name, cart_items, totals, delivery_date, salesman_name):
        """
        Generates PDF with:
        1. Real Customer Address (Top Right)
        2. Real Salesman Name (Bottom Left)
        """
        
        filename = f"Ticket_{ticket_number}.pdf"
        full_pdf_path = os.path.join(self.paths["receipts"], filename)
        barcode_path = self.paths["images"]

        # 1. FETCH CUSTOMER ADDRESS DETAILS
        try:
            parts = customer_full_name.split(" ", 1)
            first = parts[0]
            last = parts[1] if len(parts) > 1 else ""
            
            # Lookup address by name
            q = f"SELECT phone, street, city, state, zip_code FROM customers WHERE first_name = '{first}' AND last_name = '{last}'"
            res = self.db.execute_manual_query(q)
            
            if res:
                phone = res[0][0]
                street = res[0][1]
                city_state = f"{res[0][2]}, {res[0][3]} {res[0][4]}"
            else:
                phone, street, city_state = "", "", ""
        except:
            phone, street, city_state = "", "", ""

        # 2. CREATE PDF
        doc = SimpleDocTemplate(full_pdf_path, pagesize=letter, topMargin=30, bottomMargin=30)
        elements = []
        styles = getSampleStyleSheet()
        style_right = ParagraphStyle('Right', parent=styles['Normal'], alignment=2)
        style_bold = ParagraphStyle('Bold', parent=styles['Normal'], fontName='Helvetica-Bold')

        # --- HEADER ---
        company_text = [
            Paragraph("<b>Mattress Max</b>", styles['Heading1']),
            Paragraph("1225 Snow Street Suite 21", styles['Normal']),
            Paragraph("Oxford, AL 36203", styles['Normal']),
            Paragraph("Phone: 256-831-5357", styles['Normal']),
        ]
        
        date_str = datetime.now().strftime('%m/%d/%Y')
        receipt_meta = [
            Paragraph("<b>RECEIPT</b>", styles['Heading2']),
            Paragraph(f"Date: {date_str}", style_right),
            Paragraph(f"Ticket #: {ticket_number}", style_right),
        ]

        header_table = Table([[company_text, receipt_meta]], colWidths=[300, 200])
        header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('ALIGN', (1,0), (1,0), 'RIGHT')]))
        elements.append(header_table)
        elements.append(Spacer(1, 10))

        # --- INFO SECTION (Address & Notes) ---
        notes_data = [[Paragraph("Notes:", style_bold)], [""], [""], [""]]
        notes_table = Table(notes_data, colWidths=[280], rowHeights=[20, 15, 15, 15])
        notes_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.lightyellow),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ]))

        # CUSTOMER DATA BLOCK (Top Right)
        cust_data = [
            ["Customer:", customer_full_name],
            ["Phone:", phone], 
            ["Address:", street],
            ["", city_state], # City/State/Zip
            ["Delivery:", delivery_date]
        ]
        cust_table = Table(cust_data, colWidths=[70, 140])
        cust_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))

        info_wrapper = Table([[notes_table, cust_table]], colWidths=[300, 220])
        info_wrapper.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
        elements.append(info_wrapper)
        elements.append(Spacer(1, 15))

        # --- ITEMS ---
        cart_data = [['DESCRIPTION', 'LOC', 'QTY', 'PRICE', 'AMOUNT']]
        for item in cart_items:
            desc = Paragraph(f"{item['vendor']} {item['name']} ({item['size']})", styles['Normal'])
            cart_data.append([desc, "Saks", "1", f"${item['price']:,.2f}", f"${item['price']:,.2f}"])

        for _ in range(max(0, 10 - len(cart_items))):
            cart_data.append(["", "", "", "", ""])

        item_table = Table(cart_data, colWidths=[240, 60, 40, 80, 80])
        item_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('ALIGN', (2,1), (-1,-1), 'CENTER'),
            ('ALIGN', (3,1), (-1,-1), 'RIGHT'),
        ]))
        elements.append(item_table)
        elements.append(Spacer(1, 10))

        # --- FOOTER ---
        # Inject Salesman Name here
        legal_text = f"""
        All Sales are final. Serta offers a 90 day Comfort Sleep guarantee. 
        See store for details. All adjustable bases are non-refundable.
        <br/><br/>
        <b>Associate:</b> {salesman_name}
        <br/><br/>
        <b>Product Received: X _______________________</b>
        """
        footer_left = Paragraph(legal_text, styles['Normal'])

        totals_data = [
            ["SALES", f"${totals['sub']:,.2f}"],
            ["TAX RATE", f"{(totals['tax']/totals['sub']*100) if totals['sub'] > 0 else 0:.2f}%"],
            ["SUBTOTAL", f"${totals['final']:,.2f}"],
            ["DELIVERY", "$0.00"],
            ["TOTAL DUE", f"${totals['final']:,.2f}"],
        ]
        
        totals_table = Table(totals_data, colWidths=[100, 100])
        totals_table.setStyle(TableStyle([
            ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.grey),
            ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
            ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
            ('BACKGROUND', (0,-1), (-1,-1), colors.lightgrey),
        ]))

        footer_wrapper = Table([[footer_left, totals_table]], colWidths=[300, 220])
        footer_wrapper.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
        elements.append(footer_wrapper)
        
        # --- BARCODE ---
        elements.append(Spacer(1, 20))
        if os.path.exists(barcode_path):
            try:
                im = Image(barcode_path, width=450, height=100)
                elements.append(im)
            except: pass

        doc.build(elements)
        
        # OPEN
        try:
            if os.name == 'nt': 
                opener = getattr(os, 'startfile', None)
                if opener: opener(full_pdf_path)
            else:
                import subprocess
                subprocess.call(['xdg-open', full_pdf_path])
        except Exception as e:
            print(f"DEBUG: Receipt generated at: {full_pdf_path}")

    def generate_daily_spreadsheet_pdf(self):
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"EOD_Report_{today}.pdf"
        full_path = os.path.join(self.paths["receipts"], filename)

        doc = SimpleDocTemplate(full_path, pagesize=landscape(letter), topMargin=30)
        elements = []
        styles = getSampleStyleSheet()

        elements.append(Paragraph(f"End of Day Report: {today}", styles['Heading1']))
        elements.append(Spacer(1, 20))

        query = f"SELECT * FROM sales WHERE date LIKE '{today}%'"
        sales_data = self.db.execute_manual_query(query)

        if not sales_data:
            elements.append(Paragraph("No sales recorded today.", styles['Normal']))
        else:
            table_data = [['TICKET', 'ITEM', 'REP', 'PRICE', 'METHOD', 'PROFIT']]
            total_sales = 0
            total_profit = 0

            for row in sales_data:
                price = row[5] if row[5] else 0.0
                profit = row[9] if row[9] else 0.0
                
                table_data.append([
                    row[1], 
                    Paragraph(row[3], styles['Normal']),
                    row[4], 
                    f"${price:,.2f}",
                    row[12], 
                    f"${profit:,.2f}"
                ])
                total_sales += price
                total_profit += profit

            table_data.append(['', 'TOTALS', '', f"${total_sales:,.2f}", '', f"${total_profit:,.2f}"])

            t = Table(table_data, colWidths=[90, 250, 80, 80, 100, 80])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                ('GRID', (0,0), (-1,-1), 1, colors.black),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
                ('BACKGROUND', (0,-1), (-1,-1), colors.whitesmoke),
            ]))
            elements.append(t)

        doc.build(elements)
        try:
            if os.name == 'nt': 
                opener = getattr(os, 'startfile', None)
                if opener: opener(full_path)
            else:
                import subprocess
                subprocess.call(['xdg-open', full_path])
        except: pass


class PaymentMethodDialog(tb.Toplevel):
    def __init__(self, parent, options):
        super().__init__(title="Payment Method", parent=parent, size=(300, 150))
        self.result = None
        self.position_center()

        tb.Label(self, text="Select Split Payment Method:", font=("Helvetica", 10)).pack(pady=10)
        
        self.cb = tb.Combobox(self, values=options, state="readonly", font=("Helvetica", 11))
        if options: self.cb.current(0)
        self.cb.pack(fill='x', padx=20, pady=5)
        
        tb.Button(self, text="CONFIRM", bootstyle="success", command=self.confirm).pack(pady=10)
        
        self.transient(parent)
        self.grab_set()
        self.wait_window(self)
        
    def confirm(self):
        self.result = self.cb.get()
        self.destroy()