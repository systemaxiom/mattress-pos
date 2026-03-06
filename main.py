"""
================================================================================
PROJECT: System Axiom POS
VERSION: 1.0.4
AUTHOR: [Your Name/Brand Name]
DATE: February 2026
DESCRIPTION:
    A high-performance, locally-hosted Point of Sale (POS) system designed 
    specifically for multi-location mattress retail operations. 

CORE FUNCTIONALITIES:
    - Real-time inventory management with SQLite back-end.
    - Automated price-adjustment engine for mattress SKU variations.
    - Role-based access control (WAREHOUSE vs. STORE).
    - Custom reporting engine and performance tracking.

SYSTEM ARCHITECTURE:
    - Interface: ttkbootstrap (Tkinter wrapper)
    - Database: SQL (via data_helper.py)
    - Configuration: JSON-based filesystem mapping (Linux/Windows)

LICENSING:
    Proprietary Software - Developed for [Client/Company Name].
    Unauthorized copying or distribution is strictly prohibited.
================================================================================
"""

import os
import sys
import platform
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import (filedialog, simpledialog, messagebox,
                     Listbox, Text, Menu)
from data_helper import Data_Helper
from reporting import ReportingEngine
from negotiator import NegotiatorFrame
from finalize import FinalizeCommandCenter
from closer import CloserSuite

from dotenv import load_dotenv
from models import *
from utils import *
import csv
from datetime import datetime, timedelta
import sqlite3
import calendar
import json





class SystemAxiomHub:
    def __init__(self,logged_in_user = "Guest"):
        
        self.load_paths_config()
        self.db = Data_Helper()
        
        self.reporting = ReportingEngine(self.db)
        
        load_dotenv()
        self.role = os.getenv('APP_ROLE', 'WAREHOUSE')
        self.store_name = os.getenv('STORE_ID', 'ANNISTON_OFFLINE')
        self.store_theme = None
        self.traffic_count = 0
        
        self.inventory_objects = []
        self.staff_list = [] 
        self.cart = []
        self.spiff_data = {}
        self.roster_data = {}
       
        
        self.theme, self.role_title = self.get_style()
        self.app = tb.Window(
            title=f"System Axiom POS - {self.store_name}",
            themename=self.theme,
            size=(1200, 800)
        )
        self.app.withdraw()
        my_logo_path = self.paths["logo_path"]
        run_splash(self.app, my_logo_path, display_time=2500)
        self.app.after(100, self._safe_startup)
        self.current_user = logged_in_user
        self.app.title(f"System Axiom POS - {self.store_name} (User: {self.current_user})")
        
    def _safe_startup(self):
        self.app.deiconify() 
        self.setup_ui() 
        self.app.attributes('-zoomed', True)
        self.app.after(100, self.load_staff)
        self.app.after(150, self.load_spiffs)
        self.app.after(200, self.load_initial_data)
        self.app.after(300, self.update_performance_sidebar)
        self.app.after(400, self.filter_search)
        
        
    # ==========================
    # CORE CONFIGURATION
    # ==========================

    def load_paths_config(self):

        
        """Reads config.json and builds full paths."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
       
        data_dir = os.path.join(base_dir, "wharehouse_data")
        config_path = os.path.join(data_dir, "config.json")
        
        try:
            with open(config_path, 'r') as f:
                conf = json.load(f)
            
            os_key = 'linux' if platform.system().lower() == 'linux' else 'windows'
            base = conf[os_key]['base_path']
            files = conf['filenames']

            self.paths = {
                "db_path": os.path.join(base, files['db']),
                "log_path": os.path.join(base, files['logs']),
                "roster_path": os.path.join(base, files['roster']),
                "spiffs_path": os.path.join(base, files['spiffs']),
                "crew_config": os.path.join(base, files['crew_times']),
                "receipts_dir": conf[os_key]['receipts_path'],
                "logo_path": os.path.join(base, files.get('logo', 'logo.png'))
            }
            print(f"✅ Paths mapped to: {os_key}")
            
        except Exception as e:
            print(f"❌ Config Error: {e}. Using local folder fallback.")
            
            self.paths = {
                "db_path": os.path.join(data_dir, "inventory.db"),
                "logo_path": os.path.join(data_dir, "logo.png"),
                "log_path": os.path.join(data_dir, "crew_logs.json"),
                "roster_path": os.path.join(data_dir, "roster.json"),
                "spiffs_path": os.path.join(data_dir, "spiffs.json"),
                "crew_config": os.path.join(data_dir, "crew_times.json"),
                "receipts_dir": os.path.join(data_dir, "receipts")
            }

   
    
    
    def load_staff(self):
        try:
            with open(self.paths['roster_path'], 'r') as f:
              
                self.roster_data = json.load(f)
            
            self.staff_list = self.roster_data.get('associates', [])
            
            print("✅ Roster and Overhead loaded successfully.")
        except Exception as e:
            print(f"❌ Roster Error: {e}")
            self.roster_data = {}
            self.staff_list = []
            
    def load_spiffs(self):
        
        try:
           
            if os.path.exists(self.paths['spiffs_path']):
                with open(self.paths['spiffs_path'], 'r') as f:
                    self.spiff_data = json.load(f)
                print("✅ Spiff data loaded successfully.")
            else:
                print("⚠️ Spiff file not found. Defaulting to empty.")
                self.spiff_data = {}
        except Exception as e:
            print(f"❌ Error loading spiffs: {e}")
            self.spiff_data = {}      
            
            
        
    def get_style(self):
        """Determines the theme and title based on your role."""
        
        theme = "cyborg" 
        if getattr(self, 'role', 'SALES') == 'WAREHOUSE': 
            title = "MASTER HUB"
            print("test_3")
        else: 
            title = "SALES TERMINAL"
            print("test 4")
        return theme, title


    

    # ==========================
    # UI BUILDER
    # ==========================

    def setup_ui(self):
        self.del_search_val = tb.StringVar()
        self.search_col_val = tb.StringVar(value="customer_name")
        
        try:
          
            self.traffic_frame = tb.Frame(self.app, padding=10, bootstyle="dark")
            self.traffic_frame.pack(fill='x', padx=10, pady=5)
            
            tb.Label(self.traffic_frame, text="Daily Traffic:", font=("Helvetica", 12), bootstyle="inverse-dark").pack(side='left', padx=5)
            
            self.lbl_traffic = tb.Label(self.traffic_frame, text="0", font=("Helvetica", 14, "bold"), bootstyle="warning-inverse")
            self.lbl_traffic.pack(side='left', padx=5)
            
            
            tb.Button(self.traffic_frame, text="➕ Add Walk-In", bootstyle="danger-outline", command=self.add_walkin).pack(side='left', padx=15)
            tb.Button(self.traffic_frame, text="💰Generate EOD", bootstyle='success-outline', command=self.open_reports_dashboard).pack(side='left', padx=5)
            print('test 5.7')
            tb.Button(self.traffic_frame, text="✨ Import Items",bootstyle='info-outline', command=self.open_new_item_importer).pack(side='left', padx=5)
            self.theme_list = ['superhero','cyborg']
            self.store_theme = tb.Combobox(self.traffic_frame, values=self.theme_list, bootstyle='info')
            self.store_theme.pack(side='right', padx=15)
            self.store_theme.current(1)
            self.store_theme.bind("<<ComboboxSelected>>", self.change_theme)
            dep_frame = tb.Frame(self.traffic_frame, bootstyle="dark")
            dep_frame.pack(side='right', padx=10)
            print('test 5.5')
        except Exception as e:
            print(f"⚠️ UI Warning: Theme engine stalled but bypassed. Error: {e}")
       
            tb.Label(self.app, text="System Axiom Loading...").pack()
        
        
        tb.Label(dep_frame, text="Bank Deposit: $", font=("Helvetica", 11), bootstyle="inverse-dark").pack(side='left')
        
        self.deposit_entry = tb.Entry(dep_frame, width=10, bootstyle="warning")
        self.deposit_entry.pack(side='left', padx=5)
        self.deposit_entry.bind("<KeyRelease>", self.save_deposit_live)

   
        self.load_daily_stats()
        
        self.sidebar = tb.Frame(self.app, bootstyle="light", padding=10)
        self.sidebar.pack(side='left', fill='y')
        tb.Label(self.sidebar, text="Performance", font=("Helvetica", 12, "bold")).pack(pady=10)
        self.overhead_status_label = tb.Label(self.sidebar, text="Loading Stats...", wraplength=120)
        self.overhead_status_label.pack(pady=10)
        self.rsa_stats_display = tb.Frame(self.sidebar)
        self.rsa_stats_display.pack(fill='both', expand=True)
        
        # --- BATCH BUTTON  ---
        tb.Button(self.sidebar, text="📦 Batch Inventory", bootstyle="warning-outline", 
                  command=self.open_batch_inventory_tool).pack(side='bottom', pady=5)
        
        tb.Button(self.sidebar, text="🕒 Crew Clock", bootstyle="secondary-link", 
                  command=self.open_crew_clock).pack(side='bottom', pady=10)
        print('test 6')
        self.tabs = tb.Notebook(self.app, bootstyle="primary")
        self.tabs.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        print('test 7')
        # TAB 1: INVENTORY
        self.inventory_tab = tb.Frame(self.tabs)
        self.tabs.add(self.inventory_tab, text="Inventory")
        
        # LEFT COLUMN: SEARCH & TABLE
        left_panel = tb.Frame(self.inventory_tab, padding=10)
        left_panel.pack(side='left', fill='both', expand=True)
        
        # --- SEARCH FRAME START ---
        search_frame = tb.Frame(left_panel, padding=5)
        search_frame.pack(fill='x')
        
        tb.Label(search_frame, text="Live Search:").pack(side='left', padx=5)
        self.search_var = tb.StringVar()
        self.search_var.trace_add("write", self.filter_search) 
        tb.Entry(search_frame, textvariable=self.search_var, bootstyle='secondary', width=30).pack(side='left', padx=5)
        
        self.spy_icon = tb.Label(search_frame, text=" 👁️ ", font=("Helvetica", 14), bootstyle="warning-inverse", cursor="hand2")
        self.spy_icon.pack(side='left', padx=15)
        
        # Bind the Hover Events
        self.spy_icon.bind("<Enter>", self.show_cost_hover)  # Mouse Enters
        self.spy_icon.bind("<Leave>", self.hide_cost_hover)  # Mouse Leaves
        # ----------------------------------------

        self.view_state = tb.StringVar(value="INVENTORY")
        toggle_frame = tb.Frame(search_frame)
        toggle_frame.pack(side='right', padx=10)
        tb.Radiobutton(toggle_frame, text="In Stock", variable=self.view_state, value="INVENTORY", 
                       command=self.filter_search, bootstyle="info-toolbutton").pack(side='left')
        tb.Radiobutton(toggle_frame, text="To Order", variable=self.view_state, value="ORDERS", 
                       command=self.filter_search, bootstyle="warning-toolbutton").pack(side='left')
        
        self.cols = ("size", "vendor", "name", "firm", "price", "qty", "cost")
        self.tree = tb.Treeview(left_panel, bootstyle='primary', columns=self.cols, show="headings", height=12)
        print('test 8')
        
        self.tree.heading("size", text="SIZE")
        self.tree.column("size", width=60, anchor='center') 
        
        self.tree.heading("vendor", text="VENDOR")
        self.tree.column("vendor", width=100, anchor='center')
        
        self.tree.heading("name", text="NAME")
        self.tree.column("name", width=150, anchor='w') 
        
        self.tree.heading("firm", text="FIRM")
        self.tree.column("firm", width=80, anchor='center')
        
        self.tree.heading("price", text="PRICE")
        self.tree.column("price", width=80, anchor='center')
        
        self.tree.heading("qty", text="QTY")
        self.tree.column("qty", width=50, anchor='center') 
        
        self.tree.heading("cost", text="COST")
        self.tree.column("cost", width=0, stretch=False) 
        
        self.tree.pack(pady=5, fill='both', expand=True)

        self.tree.tag_configure('stock_pos', foreground='#00ff7f')
        self.tree.tag_configure('stock_zero', foreground='white')  
        self.tree.tag_configure('stock_neg', foreground='#ff4444') 
        
        cust_frame = tb.LabelFrame(left_panel, text="Customer Selection")
        cust_frame.pack(fill='x', padx=20, pady=5, ipadx=10, ipady=10)
        tb.Label(cust_frame, text="Bill To:").pack(side='left', padx=5)
        self.main_cust_search = tb.Entry(cust_frame, width=35)
        self.main_cust_search.pack(side='left', padx=5)
        self.main_cust_search.bind("<KeyRelease>", self.update_customer_dropdown)
        tb.Button(cust_frame, text="+ New Customer", command=self.open_new_customer_window, bootstyle="info").pack(side='left', padx=5)
        tb.Button(cust_frame,text="Customer Info",command=self.show_customer_data, bootstyle="warning-outline").pack(side="left",padx=5)
        
        self.cust_dropdown = Listbox(left_panel, height=4, font=("Helvetica", 11))
        self.cust_dropdown.bind("<<ListboxSelect>>", self.on_customer_selected)
        self.cust_dropdown.place_forget()
        
        self.cart_panel = tb.LabelFrame(self.inventory_tab, text=" 🛒 Active Ticket ")
        self.cart_panel.pack(side='left', fill='both', expand=True, padx=10, pady=10, ipady=10, ipadx=10)
        self.cart_listbox = Listbox(self.cart_panel, height=12, font=("Helvetica", 10))
        self.cart_listbox.pack(pady=5, fill='both', expand=True)
        self.subtotal_var = tb.StringVar(value="Subtotal: $0.00")
        tb.Label(self.cart_panel, textvariable=self.subtotal_var, font=("Helvetica", 11, "bold")).pack(pady=5)
        tb.Button(self.cart_panel, text="Remove from Cart", bootstyle="warning-outline", command=self.remove_from_cart).pack(fill='x', pady=5)
        tb.Button(self.cart_panel, text="Start Negotiation", bootstyle="success", command=self.launch_closer_suite).pack(fill='x', pady=5)
        tb.Button(self.cart_panel, text="Clear Cart", bootstyle="danger-outline", command=self.clear_cart).pack(fill='x', pady=2)

        # RIGHT COLUMN: NOTES
        self.notes_frame = tb.LabelFrame(self.inventory_tab, text=f" 📝 Post-Visit Reflection ")
        self.notes_frame.pack(side='right', fill='both', expand=False, padx=10, pady=10, ipady=15, ipadx=15)
        self.history_label = tb.Label(self.notes_frame, text="Last Note: (Search a customer)", font=('Helvetica', 9, 'italic'), wraplength=200, bootstyle="secondary")
        self.history_label.pack(anchor='w', pady=(0, 10))
        tb.Label(self.notes_frame, text="Highlights from visit:").pack(anchor='w')
        self.post_visit_notes = Text(self.notes_frame, height=12, width=30, font=('Helvetica', 10))
        self.post_visit_notes.pack(fill='both', expand=True, pady=5)
        tb.Button(self.notes_frame, text="Archive Highlights", bootstyle="info-outline", command=self.save_reflection).pack(fill='x', pady=10)
        
        
        # TAB 2: DELIVERIES
        self.delivery_tab = tb.Frame(self.tabs)
        self.tabs.add(self.delivery_tab, text="Deliveries")
        
        # Search Controls
        search_control_frame = tb.Frame(self.delivery_tab)
        search_control_frame.pack(fill='x', padx=20, pady=10)

        self.search_col_dropdown = tb.Combobox(search_control_frame, textvariable=self.search_col_val, 
                                               values=["customer_name", "item", "delivery_date"], state="readonly", width=15)
        self.search_col_dropdown.pack(side='left', padx=5)
        self.search_col_dropdown.bind("<<ComboboxSelected>>", self.on_search_change)

        self.search_entry = tb.Entry(search_control_frame, textvariable=self.del_search_val, bootstyle="info")
        self.search_entry.pack(side='left', fill='x', expand=True, padx=5)
        self.del_search_val.trace_add("write", self.on_search_change)

        
        
    
        self.del_cols = ("date", "customer", "items", "status")
        
      
        self.del_tree = tb.Treeview(
            self.delivery_tab, 
            bootstyle='info', 
            columns=self.del_cols, 
            show="headings"
        )

   
        for c in self.del_cols:
            self.del_tree.heading(c, text=c.upper())
      
            if c == "date": self.del_tree.column(c, width=120, anchor="center")
            elif c == "status": self.del_tree.column(c, width=100, anchor="center")
            elif c == "customer": self.del_tree.column(c, width=200, anchor="w")
            else: self.del_tree.column(c, width=350, anchor="w")
            
        self.del_tree.pack(fill='both', expand=True, padx=20, pady=10)
        
   
        self.del_tree.tag_configure('delivered', foreground='#00ff7f')
        self.del_tree.tag_configure('pending', foreground='#00d1ff')
        self.del_tree.tag_configure('incomplete', foreground='#ff4444')

        self.del_tree.bind("<Double-1>", self.toggle_delivery_status)
        tb.Button(self.delivery_tab, text="Refresh Schedule", command=self.load_deliveries).pack(pady=10)
        
        # --- TAB 3: FOLLOW-UPS ---
        self.followup_tab = tb.Frame(self.tabs)
        self.tabs.add(self.followup_tab, text="Follow-Ups")
        
        cols_follow = ("name", "phone", "visit_date")
  
        self.follow_tree = tb.Treeview(self.followup_tab, bootstyle='info', columns=cols_follow, show="headings")

        for c in cols_follow:
            self.follow_tree.heading(c, text=c.upper())
            self.follow_tree.column(c, width=150, anchor='center')
        
        self.follow_tree.pack(pady=20, padx=20, fill='both', expand=True)
        
        tb.Label(self.followup_tab, text="Right-click a name to see visit highlights for your handwritten card.", 
                 font=('Helvetica', 10, 'italic')).pack(pady=5)
        
        tb.Button(self.followup_tab, text="Check for Today's Reminders", 
                  bootstyle="info-outline", command=self.load_reminders).pack(pady=10)
        
      
        self.follow_tree.bind("<Button-3>", self.show_reminder_details)
        
        # CONTEXT MENU
        self.context_menu = Menu(self.app, tearoff=0)
        self.context_menu.add_command(label="💰 Record Sale", command=self.add_to_cart) 
        self.context_menu.add_command(label="✏️ Edit Item", command=self.open_edit_item_window) # <--- ADD THIS LINE
        self.context_menu.add_command(label="❌ Delete Item", command=self.delete_selected_item)
        self.tree.bind("<Button-3>", self.show_context_menu)
        
        
        
    # ==========================
    # LOGIC METHODS
    # ==========================

    def change_theme(self, event=None):
        selected_theme = self.store_theme.get()
        if selected_theme: self.app.style.theme_use(selected_theme)
        
    

    def get_traffic_file_path(self):
        """Bypasses SQLiteCloud pathing to find the local JSON store."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_dir, "wharehouse_data", "daily_traffic.json")
    
    def update_daily_json(self, key_suffix, value):
        """Universal helper to save traffic or deposits."""
        today_str = datetime.now().strftime("%Y-%m-%d")
        t_path = self.get_traffic_file_path()
        
        data = {}
        if os.path.exists(t_path):
            try:
                with open(t_path, 'r') as f:
                    data = json.load(f)
            except: pass
        
      
        full_key = f"{today_str}{key_suffix}"
        data[full_key] = value
        
        with open(t_path, 'w') as f:
            json.dump(data, f, indent=4)
    

    def save_deposit_live(self, event=None):
        """Saves the deposit amount as you type."""
        val = self.deposit_entry.get()
    
        self.update_daily_json("_deposit", val)

    
    def load_daily_stats(self):
        """Populates labels at startup from the JSON."""
        today_str = datetime.now().strftime("%Y-%m-%d")
        t_path = self.get_traffic_file_path()
        
        if os.path.exists(t_path):
            try:
                with open(t_path, 'r') as f:
                    data = json.load(f)
                    
                    # Update Traffic Label
                    count = data.get(today_str, 0)
                    self.lbl_traffic.config(text=str(count))
                    
                    # Update Deposit Entry
                    deposit = data.get(f"{today_str}_deposit", "0.00")
                    self.deposit_entry.delete(0, 'end')
                    self.deposit_entry.insert(0, str(deposit))
            except: pass


    def save_reflection(self):
        full_name = self.main_cust_search.get().strip()
        highlights = self.post_visit_notes.get("1.0", "end-1c").strip()
        if not full_name: return
        
        try:
            parts = full_name.split(" ", 1)
            first = parts[0]
            last = parts[1] if len(parts) > 1 else ""
            
            # CLEAN REFACTOR:
            self.db.update_table(
                "customers", 
                {"highlights": highlights}, 
                "first_name=? AND last_name=?", 
                (first, last)
            )
            
            messagebox.showinfo("Success", f"Highlights archived for {full_name}.")
            self.post_visit_notes.delete("1.0", "end")
        except Exception as e:
            messagebox.showerror("DB Error", f"Could not save: {e}")

    def load_reminders(self):
        from datetime import datetime, timedelta
        
        self.follow_tree.delete(*self.follow_tree.get_children())
        
      
        target_date = (datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d')
        
   
        results = self.db.select_data(
            table_name='customers', 
            columns='first_name, last_name, phone, last_visit_date',
            where_clause='last_visit_date = ?',
            where_args=(target_date,)
        )
        
        if results:
            for row in results:
                try:
                 
                    name = f"{row[0]} {row[1]}"
                    phone = row[2] or "No Phone"
                    date = row[3]
                    
              
                    self.follow_tree.insert('', 'end', values=(name, phone, date))
                    
                except Exception as e:
                    print(f"🚨 Reminder Row Error: {e} | Skipping row...")

    def show_reminder_details(self, event):
        item = self.follow_tree.identify_row(event.y)
        if not item: return
        vals = self.follow_tree.item(item)['values']
        full_name = vals[0]
        
  
        parts = full_name.split(" ", 1)
        first = parts[0]
        last = parts[1] if len(parts) > 1 else ""

        try:
       
            results = self.db.select_data(
                table_name="customers",
                columns="highlights, street, city, state, zip_code",
                where_clause="first_name = ? AND last_name = ?",
                where_args=(first, last)
            )
            
            if results:
              
                customer = results[0] 
                
            
                notes = customer[0] or "No previous highlights."
                street = customer[1] or ""
                city = customer[2] or ""
                state = customer[3] or ""
                zip_code = customer[4] or ""
                
                address = f"{street}, {city} {state} {zip_code}".strip()
                
           
                messagebox.showinfo(
                    "Handwritten Card Info", 
                    f"Customer: {full_name}\nAddress: {address}\n--------------------------\nHIGHLIGHTS: {notes}"
                )
            else:
                messagebox.showwarning("Not Found", "Could not find this customer's details.")
                
        except Exception as e:
            messagebox.showerror("Database Error", f"Error loading reminder details: {e}")
     
    
    def open_new_customer_window(self):
        new_win = tb.Toplevel(title="Add New Customer")
        new_win.geometry("450x650")
        container = tb.Frame(new_win, padding=20)
        container.pack(fill='both', expand=True)

        # NEW FIELDS
        fields = {}
        labels = ["First Name", "Last Name", "Phone", "Street Address", "City", "State", "Zip Code", "Email"]
        
        for lbl in labels:
            tb.Label(container, text=lbl + ":").pack(anchor='w')
            ent = tb.Entry(container)
            ent.pack(fill='x', pady=(0, 10))
            fields[lbl] = ent

        def save_and_select():
            f_name = fields["First Name"].get().strip()
            l_name = fields["Last Name"].get().strip()
            
            if not f_name:
                messagebox.showwarning("Missing Info", "First Name is required!")
                return
            
          
            customer_payload = {
                "first_name": f_name,
                "last_name": l_name,
                "phone": fields["Phone"].get().strip(),
                "street": fields["Street Address"].get().strip(),
                "city": fields["City"].get().strip(),
                "state": fields["State"].get().strip(),
                "zip_code": fields["Zip Code"].get().strip(),
                "email": fields["Email"].get().strip(),
                "last_visit_date": datetime.now().strftime("%Y-%m-%d")
            }
            
            # Send it to the helper
            self.db.insert_data('customers', customer_payload)
            
            full_display = f"{f_name} {l_name}"
            self.main_cust_search.delete(0, 'end')
            self.main_cust_search.insert(0, full_display)
            self.history_label.config(text="Last Note: New Customer - No history yet.")
            new_win.destroy()
            messagebox.showinfo("Success", f"{full_display} added to System!")

        tb.Button(container, text="Save & Select", bootstyle="success", command=save_and_select).pack(pady=20)

    def update_customer_dropdown(self, event):
        term = self.main_cust_search.get().lower().strip()
        self.post_visit_notes.delete("1.0", "end")
        self.history_label.config(text="Last Note: (Searching...)")

        if len(term) < 2:
            self.cust_dropdown.place_forget() 
            return

        # Setup the safe search parameter with wildcards
        search_param = f"%{term}%"

        # RULE 2: Selects use select_data with args
        results = self.db.select_data(
            table_name='customers',
            columns='first_name, last_name, phone',
            where_clause="lower(first_name) LIKE ? OR lower(last_name) LIKE ? OR phone LIKE ?",
            where_args=(search_param, search_param, search_param)
        )

        if results:
            self.cust_dropdown.delete(0, 'end')
            for r in results:
               
                self.cust_dropdown.insert('end', f"{r['first_name']} {r['last_name']} | {r['phone']}")
            self.cust_dropdown.place(in_=self.main_cust_search, x=0, rely=1.0, relwidth=1.0) 
            self.cust_dropdown.lift()
        else:
            self.cust_dropdown.place_forget()

    def on_customer_selected(self, event):
        if not self.cust_dropdown.curselection(): return
        full_text = self.cust_dropdown.get(self.cust_dropdown.curselection())
        
     
        name_part = full_text.split(" | ")[0].strip()
        self.main_cust_search.delete(0, 'end')
        self.main_cust_search.insert(0, name_part)
        self.cust_dropdown.place_forget()
        
        # Fetch Highlights
        try:
            parts = name_part.split(" ", 1)
            first = parts[0]
            last = parts[1] if len(parts) > 1 else ""
        
    
            results = self.db.select_data(
                table_name='customers',
                columns='highlights',
                where_clause="first_name = ? AND last_name = ?",
                where_args=(first, last)
            )
            
        
            if results and results[0][0]:
                self.history_label.config(text=f"Last Note: {results[0][0]}") 
            else:
                self.history_label.config(text="Last Note: No previous highlights.")
                
        except Exception as e:
            self.history_label.config(text="Last Note: (Error fetching data)")
            
    def show_customer_data(self):
        selection = self.cust_dropdown.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a customer first.")
            return
            
        index = selection[0]
     
        selected_name = self.cust_dropdown.get(index).split('|')[0].strip() 
        
        try:
         
            results = self.db.select_data(
                table_name='customers',
                columns="first_name, last_name, phone, email, last_visit_date, street, city, state, zip_code",
                where_clause="first_name || ' ' || last_name = ?",
                where_args=(selected_name,) 
            )
            
            if results:
                customer = results[0] 
                
              
                c_fname = customer[0]
                c_lname = customer[1]
                c_phone = customer[2] or "No Phone"
                c_email = customer[3] or "No Email"
                c_visit = customer[4] or "Unknown"
                c_street = customer[5] or "No Street Provided"
                c_city = customer[6] or ""
                c_state = customer[7] or ""
                c_zip = customer[8] or ""
                

                if c_city or c_state or c_zip:
                    address = f"{c_street}\n{c_city}, {c_state} {c_zip}".strip()
                else:
                    address = c_street
                
         
                info_text = (
                    f"Name: {c_fname} {c_lname}\n"
                    f"Phone: {c_phone}\n"
                    f"Email: {c_email}\n"
                    f"Last Visit: {c_visit}\n\n"
                    f"Delivery Address:\n{address}"
                )
                
                messagebox.showinfo(f"Customer Data: {selected_name}", info_text)
                
            else:
                messagebox.showerror("Not Found", f"Could not find database records for '{selected_name}'.")
                
        except Exception as e:
            messagebox.showerror("Database Error", f"Error fetching customer data: {e}")

    def launch_closer_suite(self):
        from closer import CloserSuite
        
        CloserSuite(
            parent=self.app,
            cart=self.cart,
            spiff_data=self.spiff_data,
            roster_data=self.roster_data, # Loaded in load_staff
            on_finalize=self.push_to_final_checkout,
            store_name=self.store_name
        )
        
    def load_deliveries(self):
        """The cleaned-up, mandatory-date version of load_deliveries."""
        self.del_tree.delete(*self.del_tree.get_children())
        
       
        query = "SELECT id, delivery_date, customer_name, item, status FROM sales"
        
        try:
            rows = self.db.execute_manual_query(query)
            if rows:
                for r in rows:
                    db_id = r[0]
                    d_date = str(r[1]) if r[1] else "No Date"
                    
           
                    raw_name = r[2]
                    if not raw_name or str(raw_name).strip() == "":
                        c_name = "UNKNOWN CUSTOMER"
                    else:
                        c_name = str(raw_name)

                    i_name = str(r[3]) if r[3] else "Item Unknown"
                    current_status = str(r[4]) if r[4] else "Pending"
                    
                    # Tagging for colors
                    tag = "pending"
                    if current_status == "Delivered":
                        tag = 'delivered'
                    elif current_status == "Incomplete":
                        tag = 'incomplete'
                    
                    self.del_tree.insert(
                        '', 'end', 
                        iid=str(db_id), # Ensure the ID is a string
                        values=(d_date, c_name, i_name, current_status), 
                        tags=(tag,)
                    )
            print(f"✅ Warehouse Schedule: {len(self.del_tree.get_children())} items loaded.")
        except Exception as e:
            print(f"❌ SQL Execution Error: {e}")

            
            
            
            
    def on_search_change(self, *args):
        """Filters deliveries based on the selected column and search text."""
        search_text = self.del_search_val.get().strip().lower()
        search_column = self.search_col_val.get() 
        
        self.del_tree.delete(*self.del_tree.get_children())

  
        wildcard = f"%{search_text}%"
        
      
        query = f"""
            SELECT id, delivery_date, customer_name, item, status 
            FROM sales 
            WHERE {search_column} LIKE ? 
            AND delivery_date IS NOT NULL 
            AND delivery_date != ''
            ORDER BY delivery_date DESC
        """

        try:
            rows = self.db.execute_manual_query(query, (wildcard,))
            if rows:
                for r in rows:
                    db_id = r[0]
                    current_status = r[4] if r[4] else "Pending"
                    if current_status == "Delivered": tag = 'delivered'
                    elif current_status == "Incomplete":  tag = 'incomplete'
                    else: tag = 'pending'
                        
                    
                    self.del_tree.insert(
                        '', 'end', 
                        iid=db_id, 
                        values=(r[1], r[2], r[3], current_status), 
                        tags=(tag,)
                    )
        except Exception as e:
            print(f"❌ Search Error: {e}")
            
            
    def toggle_delivery_status(self, event):
        """Rotates status: Pending -> Incomplete -> Delivered"""
        # 1. Identify which row was clicked
        item_id = self.del_tree.identify_row(event.y)
        if not item_id:
            return

        # 2. Get current values (Status is in the 4th column, index 3)
        current_values = self.del_tree.item(item_id, 'values')
        current_status = current_values[3]
        
        # 3. Rotate the status logic
        if current_status == "Pending":
            new_status = "Incomplete"
        elif current_status == "Incomplete":
            new_status = "Delivered"
        else:
            new_status = "Pending"
        
        try:
       
            update_sql = "UPDATE sales SET status = ? WHERE id = ?"
            self.db.execute_manual_query(update_sql, (new_status, item_id))
            print(f"🔄 Ticket {item_id} changed to {new_status}")
            self.load_deliveries()
            
        except Exception as e:
            print(f"❌ Toggle Failed: {e}")
                
                
   
    
      
    
    def filter_search(self, *args):
        query = self.search_var.get().strip().lower()
        view_mode = self.view_state.get() # "INVENTORY" or "ORDERS"
        
        # Clear current list
        self.tree.delete(*self.tree.get_children())
        self.inventory_objects = [] 

        try:
            
            search_param = f"%{query}%"
            
            
            where_str = "(lower(name) LIKE ? OR lower(vendor) LIKE ? OR lower(size) LIKE ?)"
            where_params = [search_param, search_param, search_param] 
            
            if view_mode == "ORDERS":
                where_str += " AND count < 0"
            rows = self.db.select_data(
                table_name='inventory', 
                where_clause=where_str, 
                where_args=tuple(where_params)
        )
            
            # 5. Build the UI
            if rows:
                for r in rows:
                    
                    m = InventoryObject(
                        r['id'], r['vendor'], r['name'], r['attribute'], 
                        r['cost'], r['price'], r['size'], r['count'], r['sku']
                    )
                    self.inventory_objects.append(m)
                    
                    # Format Money
                    display_price = f"${m.price:,.0f}"
                    display_cost = f"${m.cost:,.0f}"
                    
                    # Determine Color Tag
                    if m.count > 0:
                        my_tag = 'stock_pos'   # In Stock
                    elif m.count < 0:
                        my_tag = 'stock_neg'   # Oversold
                    else:
                        my_tag = 'stock_zero'  # Out (but not owed)

                    # Insert into the visual tree
                    self.tree.insert('', 'end', values=(
                        m.size, m.vendor, m.name, m.attribute, display_price, m.count, display_cost
                    ), tags=(my_tag,))
                    
        except Exception as e:
            print(f"Filter Search DB Error: {e}")

         

        

    def load_initial_data(self):
        self.inventory_objects = []
        try:
            cols = "id, vendor, name, attribute, cost, price, size, count, sku"
            rows = self.db.select_data("inventory", columns=cols)
            
            if rows: # Check if rows exist before looping
                for r in rows:
                    self.inventory_objects.append(InventoryObject(*r))
            
         
            self.update_performance_sidebar() 
            
        except Exception as e:
            print(f"Data Load Error: {e}")

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
            self.app.bind("<Button-1>", self.close_context_menu, add="+")

    def close_context_menu(self, event):
        """Forces the menu to close when you click away."""
        self.context_menu.unpost()
        
        self.app.unbind("<Button-1>")

    def add_to_cart(self):
        # 1. Get Selection
        selected = self.tree.selection()
        if not selected: return
        
        try:
            row_id = selected[0]
            index = self.tree.index(row_id)
            item = self.inventory_objects[index] 
        except (IndexError, ValueError):
            messagebox.showerror("Error", "Could not identify selected item.")
            return

     
        self.cart.append({
            "vendor": item.vendor,
            "name": item.name,
            "size": item.size,
            "sku": item.sku,
            "price": item.price, # MSRP/Starting Price
            "cost": item.cost,
            "attribute": item.attribute,
        })
        
  
        self.refresh_cart_display()
        print(f"Staged: {item.name}")



        

    def remove_from_cart(self):
        selection = self.cart_listbox.curselection()
        if not selection:
            messagebox.showwarning("Selection", "Click an item in the cart to remove it.")
            return
        index = selection[0]
        self.cart.pop(index)
        self.refresh_cart_display()

    def refresh_cart_display(self):
        self.cart_listbox.delete(0, 'end')
        total = 0
        for item in self.cart:
         
            self.cart_listbox.insert('end', f"{item['size']} {item['name']} - ${item['price']:,.2f}")
            total += item['price']
        self.subtotal_var.set(f"Subtotal: ${total:,.2f}")

    def delete_selected_item(self):
        # 1. Get the row the user right-clicked on
        selected = self.tree.selection()
        if not selected:
            return

        # 2. Extract the visual values for the popup box
        values = self.tree.item(selected[0], 'values')
        size = values[0]
        vendor = values[1]
        name = values[2]
        
        # 3. Ask for confirmation first (The Buffer!)
        confirm = messagebox.askyesno(
            "Confirm Delete", 
            f"Are you sure you want to PERMANENTLY remove:\n\n"
            f"{vendor} {name}\n"
            f"(Size: {size})\n\n"
            f"This cannot be undone.",
            parent=self.app  
        )

        # 4. Add Pin for Manager Overide 
        if confirm:
            if not self.check_manager_override(): 
                return
            
            
            index = self.tree.index(selected[0])
            item_to_delete = self.inventory_objects[index]
            db_id = item_to_delete.id 
            
          
            success = self.db.delete_data('inventory', "id = ?", (db_id,))
            
            if success:
                self.filter_search() 
                messagebox.showinfo("Success", f"Item '{name}' has been removed.")
            else:
                messagebox.showerror("Error", "The delete command failed. Check database connection.")
            

    def clear_cart(self):
        self.cart = []
        self.cart_listbox.delete(0, 'end')
        self.subtotal_var.set("Subtotal: $0.00")

    

    def open_negotiator(self):
        """ The hand-off from Main to the Negotiator """
        if not self.cart:
            messagebox.showwarning("Empty Cart", "No mattresses in the pen yet!")
            return

        NegotiatorFrame(
            cart_items=self.cart,
            spiff_data=self.spiff_data, # Already a dict
            roster_data=self.roster_data, # Already a dict
            on_finalize=self.push_to_final_checkout
        )
        
        

    def push_to_final_checkout(self, final_cart):
        """This is the callback that gets the updated prices from Negotiator."""
        self.cart = final_cart
        print("New prices accepted. Moving to payment...")

        cust_name = self.main_cust_search.get().strip() or "Walk-in Customer"
        
        FinalizeCommandCenter(
            parent=self,
            cart=self.cart,
            db_helper=self.db,
            spiff_data=self.spiff_data,
            roster=self.roster_data,           
            customer_name=cust_name,           
            on_success_callback=self.handle_sale_success,
            store_name=self.store_name   # FIX: Pass the store name to Finalize to sort the employees!
        )
    
    
    def handle_sale_success(self):
        """The Final Step: Cleans the slate"""
        self.cart = []               
        self.refresh_cart_display()  
        self.filter_search()         
        print("✅ System Axiom: Inventory synced and cart cleared.")


    # ==========================
    # REPORTING & CREW
    # ==========================
    
    def get_salesperson_stats(self, name):
        now = datetime.now()
        _, days_in_month = calendar.monthrange(now.year, now.month)

        store_key = "Oxf" if "OXF" in self.store_name.upper() else "Saks"
        emp_key = "oxf_employees" if store_key == "Oxf" else "employees"

        schedule = []
        store_target = 17500.00
        
        # 1. Load JSON data safely
        try:
            with open(self.paths['roster_path'], 'r') as f:
                roster_data = json.load(f)
            store_target = roster_data.get('overhead', {}).get(store_key, 17500.00)
            schedule = roster_data.get(emp_key, {}).get(name, [])
        except Exception as e:
            print(f"Roster Load Error: {e}")

        # 2. Query sales to see what they Made
        query = f"SELECT SUM(profit) FROM sales WHERE salesman = '{name}' AND date LIKE '{now.strftime('%Y-%m')}%'"
        result = self.db.execute_manual_query(query)
        made = float(result[0][0]) if result and result[0] and result[0][0] else 0.0

        # 3. Check schedule to see what they Need
        if not schedule:
           
            return 0.0, made

        daily_overhead = store_target / days_in_month
        days_worked = sum(1 for i in range(1, now.day + 1)
                          if datetime(now.year, now.month, i).strftime("%A") in schedule)
        needs = days_worked * daily_overhead

        return needs, made

    def update_performance_sidebar(self):

        for widget in self.rsa_stats_display.winfo_children():
            widget.destroy()

        try:
            now = datetime.now()
            month_str = now.strftime("%Y-%m")
            
        
            query = f"SELECT DISTINCT salesman FROM sales WHERE date LIKE '{month_str}%'"
            active_reps = self.db.execute_manual_query(query)
            
            if not active_reps:
                tb.Label(self.rsa_stats_display, text="No sales recorded yet.", font=("Helvetica", 9, "italic")).pack(pady=10)
                return

          
            for row in active_reps:
                rsa_name = row[0]
                if not rsa_name: continue

                needs, made = self.get_salesperson_stats(rsa_name)

                frame = tb.Frame(self.rsa_stats_display, padding=5)
                frame.pack(fill='x')

                tb.Label(frame, text=f"{rsa_name} Needs: ${needs:,.2f}", font=("Helvetica", 9)).pack(anchor='w')
                color = "success" if made >= needs else "warning"
                tb.Label(frame, text=f"{rsa_name} Made: ${made:,.2f}", 
                         font=("Helvetica", 9, "bold"), bootstyle=color).pack(anchor='w')
                
                tb.Separator(self.rsa_stats_display).pack(fill='x', pady=5)

            # 4. Refresh the Store's Overall Overhead Label
            self.refresh_overhead_display()

        except Exception as e:
            print(f"❌ Sidebar Update Error: {e}")

    def refresh_overhead_display(self):
        try:
            now = datetime.now()
            store_key = "Oxf" if "OXF" in self.store_name.upper() else "Saks"

            # 1. Get Store Target from JSON
            with open(self.paths['roster_path'], 'r') as f:
                roster_data = json.load(f)
            target_val = roster_data.get('overhead', {}).get(store_key, 17500.00)

            # 2. Query TOTAL STORE PROFIT from the DB
            query = f"SELECT SUM(profit) FROM sales WHERE date LIKE '{now.strftime('%Y-%m')}%'"
            result = self.db.execute_manual_query(query)
            profit_val = float(result[0][0]) if result and result[0] and result[0][0] else 0.0

            # 3. Calculate difference
            diff = profit_val - target_val

            # 4. Update the Label
            if diff < 0:
                status_text = f"{store_key.upper()} OVERHEAD NOT MET: -${abs(diff):,.2f}\n(${profit_val:,.0f} of ${target_val:,.0f})"
                status_color = "danger"
            else:
                status_text = f"{store_key.upper()} OVERHEAD MET! +${diff:,.2f}\n(${profit_val:,.0f} of ${target_val:,.0f})"
                status_color = "success"

            if hasattr(self, 'overhead_status_label'):
                self.overhead_status_label.config(text=status_text, bootstyle=status_color)

        except Exception as e:
            print(f"Overhead Display Error: {e}")

            
    
    
    def open_crew_clock(self):
        clock_pop = tb.Toplevel(title="Crew Hub")
        clock_pop.geometry("350x450")
        container = tb.Frame(clock_pop, padding=20)
        container.pack(fill='both', expand=True)

        try:
            with open(self.paths['crew_config'], 'r') as f:
                data = json.load(f)
                # Use a local variable 'names' to feed the UI
                names = data.get('crew', []) 
                self.crew_list = names 
        except Exception as e:
            print(f"❌ Actual Error: {e}") 
            names = ["no crew found"]
            self.crew_list = names

        tb.Label(container, text="Select Crew Member:", font=("Helvetica", 12)).pack(pady=10)
        name_combo = tb.Combobox(container, values=names, state="readonly", font=("Helvetica", 12))
        name_combo.pack(pady=5, fill='x')

        def log_time(status):
            name = name_combo.get()
            if not name: return
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_entry = {"name": name, "status": status, "time": timestamp}
            log_file = self.paths['log_path']
            logs = []
            if os.path.exists(log_file):
                try:
                    with open(log_file, "r") as f:
                        logs = json.load(f)
                except:
                    logs = []
            try:
                logs.append(new_entry)
                with open(log_file, "w") as f:
                    json.dump(logs, f, indent=4)
                messagebox.showinfo("Success", f"{name} Clocked {status} at {timestamp}")
                clock_pop.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Could not save log: {e}")

        tb.Button(container, text="CLOCK IN", bootstyle="success", command=lambda: log_time("IN")).pack(fill='x', pady=10)
        tb.Button(container, text="CLOCK OUT", bootstyle="danger", command=lambda: log_time("OUT")).pack(fill='x', pady=10)
        tb.Separator(container).pack(fill='x', pady=15)
        tb.Button(container, text="View Weekly Hours", bootstyle="info-outline", command=self.show_crew_report).pack(fill='x', pady=5)

    def open_batch_inventory_tool(self):
        """
        Opens a tool to bulk-add inventory.
        v4: TOKEN MATCHING + DEBUG LOGS + UNIVERSAL DATA HELPER
        """
        
        tool_win = tb.Toplevel(title="Batch Inventory Manager")
        tool_win.geometry("800x600")
        
        tb.Label(tool_win, text="Batch Inventory Tool", font=("Helvetica", 16, "bold")).pack(pady=10)
        tb.Label(tool_win, text="Use for Truck Deliveries or Audits", bootstyle="secondary").pack()
        
        info_frame = tb.Frame(tool_win, padding=10, bootstyle="info")
        info_frame.pack(fill='x', padx=20, pady=10)
        
        instructions = """
        File Format (CSV): [Identifier, Quantity]
        • Identifier: SKU (Best) OR Key Words (e.g. 'ProAdapt Medium Queen')
        • Logic: Order doesn't matter! 'Queen Medium' matches 'Medium Queen'
        """
        tb.Label(info_frame, text=instructions, justify="left", foreground="white").pack()

        # PREVIEW TABLE
        cols = ("id", "name", "old_qty", "change", "new_qty")
        preview_tree = tb.Treeview(tool_win, columns=cols, show="headings", height=10)
        
        preview_tree.heading("id", text="Search Term")
        preview_tree.heading("name", text="Matched Item")
        preview_tree.heading("old_qty", text="Current")
        preview_tree.heading("change", text="Change")
        preview_tree.heading("new_qty", text="New Total")
        
        preview_tree.column("id", width=150)
        preview_tree.column("name", width=300)
        preview_tree.column("old_qty", width=60)
        preview_tree.column("change", width=60)
        preview_tree.column("new_qty", width=60)
        
        preview_tree.pack(fill='both', expand=True, padx=20, pady=10)

        self.pending_updates = [] 

        def clean_token(s):
            return "".join(e for e in str(s).lower() if e.isalnum())

        def load_csv():
            
            
            filename = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
            if not filename: return
            
            preview_tree.delete(*preview_tree.get_children())
            self.pending_updates = []
            log_messages = [f"--- BATCH LOG START: {datetime.now()} ---"]
            
            try:
                with open(filename, 'r') as f:
                    reader = csv.reader(f)
                    next(reader, None) # Skip header
                    
                    for row_idx, row in enumerate(reader):
                        if len(row) < 2: continue
                        
                        raw_identifier = row[0].strip()
                        search_parts = raw_identifier.split()
                        search_tokens = set(clean_token(p) for p in search_parts if p.strip())
                        
                        try:
                            change_qty = int(row[1].strip())
                        except ValueError:
                            log_messages.append(f"Row {row_idx+2}: ERROR - Invalid Quantity")
                            continue 
                        
                        candidates = []
                        for i in self.inventory_objects:
                            # Exact SKU
                            if clean_token(i.sku) == clean_token(raw_identifier):
                                candidates = [i]
                                break 
                            # Token Match
                            i_name_parts = i.name.split()
                            i_tokens = set(clean_token(p) for p in i_name_parts if p.strip())
                            if search_tokens.issubset(i_tokens):
                                candidates.append(i)
                        
                        item = None
                        if len(candidates) == 1:
                            item = candidates[0]
                        elif len(candidates) > 1:
                            candidates.sort(key=lambda x: len(x.name))
                            item = candidates[0]

                        if item:
                            
                            new_total = item.count + change_qty
                            preview_tree.insert('', 'end', values=(
                                raw_identifier, item.name, item.count, f"{change_qty:+}", new_total
                            ))
                            self.pending_updates.append((new_total, item.sku))
                        else:
                            preview_tree.insert('', 'end', values=(raw_identifier, "NOT FOUND", "--", "--", "--"), tags=('error',))
                            log_messages.append(f"Row {row_idx+2}: No match for '{raw_identifier}'")

                preview_tree.tag_configure('error', foreground='red')
                
                # Write Log
                log_path = os.path.join(os.path.dirname(self.paths['db_path']), "batch_debug_log.txt")
                with open(log_path, "w") as f: f.write("\n".join(log_messages))
                
                if self.pending_updates:
                    btn_commit.config(state="normal", text=f"CONFIRM {len(self.pending_updates)} UPDATES")
                else:
                    messagebox.showwarning("Review Needed", "See batch_debug_log.txt for details.")

            except Exception as e:
                messagebox.showerror("File Error", f"Could not read CSV: {e}")

        def commit_changes():
            if not self.pending_updates: return
            try:
               
                for new_qty, sku in self.pending_updates:
                    # Package the change into a dictionary
                    update_payload = {"count": new_qty}
                    
                    # Hand it to the helper with the specific SKU
                    self.db.update_data('inventory', update_payload, "sku = ?", (sku,))
                
                messagebox.showinfo("Success", "Inventory Updated Successfully!")
                self.load_initial_data()
                self.filter_search()
                tool_win.destroy()
            except Exception as e:
                messagebox.showerror("Database Error", f"Update failed: {e}")

        btn_box = tb.Frame(tool_win, padding=20)
        btn_box.pack(fill='x', side='bottom')
        tb.Button(btn_box, text="1. Load File (.csv)", bootstyle="info-outline", command=load_csv).pack(side='left', fill='x', expand=True, padx=5)
        
        btn_commit = tb.Button(btn_box, text="Commit Changes", bootstyle="success", state="disabled", command=commit_changes)
        btn_commit.pack(side='left', fill='x', expand=True, padx=5)

    def open_new_item_importer(self):
        """
        Tool to CREATE new inventory items from a master CSV.
        """
        import_win = tb.Toplevel(title="Import New Inventory")
        import_win.geometry("800x600")
        
        tb.Label(import_win, text="Initial Inventory Importer", font=("Helvetica", 16, "bold")).pack(pady=10)
        tb.Label(import_win, text="Use this to CREATE new items from scratch.", bootstyle="danger").pack()
        
        info_frame = tb.Frame(import_win, padding=10, bootstyle="secondary")
        info_frame.pack(fill='x', padx=20, pady=10)
        
        instructions = """
        REQUIRED CSV COLUMNS:
        SKU, Vendor, Name, Size, Style, Cost, Price, Qty
        
        * Order of columns does not matter.
        * Headers must match the names above exactly.
        """
        tb.Label(info_frame, text=instructions, justify="left").pack()

        # PREVIEW
        cols = ("sku", "name", "vendor", "price", "qty")
        tree = tb.Treeview(import_win, columns=cols, show="headings", height=12)
        
        tree.heading("sku", text="SKU")
        tree.heading("name", text="Name")
        tree.heading("vendor", text="Vendor")
        tree.heading("price", text="Price")
        tree.heading("qty", text="Qty")
        
        tree.column("sku", width=100)
        tree.column("name", width=250)
        tree.column("vendor", width=120)
        tree.column("price", width=80)
        tree.column("qty", width=60)
        
        tree.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.new_items_payload = []

        def load_csv():
            
            filename = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
            if not filename: return
            
            tree.delete(*tree.get_children())
            self.new_items_payload = []
            
            try:
                import csv
                with open(filename, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    # Normalize headers
                    reader.fieldnames = [name.strip().lower() for name in reader.fieldnames]
                    
                    for row in reader:
                        # 1. SKIP EMPTY ROWS
                        raw_sku = row.get('sku')
                        if not raw_sku or not str(raw_sku).strip():
                            continue

                        try:
                            # 2. Get Values Safely
                            sku = str(raw_sku).strip()
                            vendor = str(row.get('vendor') or 'Unknown').strip()
                            name = str(row.get('name') or 'Unknown Item').strip()
                            size = str(row.get('size') or 'N/A').strip()
                            style = str(row.get('attribute') or 'Standard').strip()
                            
                            # 3. Clean Numbers
                            c_val = str(row.get('cost') or '0').replace('$','').replace(',','').strip()
                            cost = float(c_val) if c_val else 0.0
                            
                            p_val = str(row.get('price') or '0').replace('$','').replace(',','').strip()
                            price = float(p_val) if p_val else 0.0
                            
                            q_val = str(row.get('qty') or '0').replace(',','').strip()
                            qty = int(float(q_val)) if q_val else 0
                            
                            # 4. Add to Preview
                            tree.insert('', 'end', values=(sku, name, vendor, f"${price:,.2f}", qty))
                            
                            # PACKING THE TUPLE
                            item_data = (vendor, name, style, cost, price, size, qty, sku)
                            self.new_items_payload.append(item_data)
                            
                        except ValueError:
                            continue 

                if self.new_items_payload:
                    btn_save.config(state="normal", text=f"CREATE {len(self.new_items_payload)} NEW ITEMS")
                else:
                    messagebox.showwarning("Error", "No valid data found.")

            except Exception as e:
                messagebox.showerror("File Error", f"Could not read CSV: {e}")

        def save_to_db():
            if not self.new_items_payload: return
            
            try:
                for item in self.new_items_payload:
                    
                    data_to_save = {
                        "vendor": item[0],
                        "name": item[1],
                        "attribute": item[2], 
                        "cost": item[3],
                        "price": item[4],
                        "size": item[5],
                        "count": item[6],  
                        "sku": item[7]
                    }
                    
                    
                    self.db.insert_data('inventory', data_to_save)
                
                messagebox.showinfo("Success", "Database populated successfully!")
                self.load_initial_data() 
                self.filter_search()     
                import_win.destroy()     
                
            except Exception as e:
                messagebox.showerror("Database Error", f"Import failed: {e}")

        # BUTTONS
        btn_box = tb.Frame(import_win, padding=20)
        btn_box.pack(fill='x', side='bottom')
        
        tb.Button(btn_box, text="1. Select Master CSV", bootstyle="info", command=load_csv).pack(side='left', padx=10)
        
       
        btn_save = tb.Button(btn_box, text="Create Items", bootstyle="success", state="disabled", command=save_to_db)
        btn_save.pack(side='right', padx=10)

        
        
    def add_walkin(self):
        try:
            current_count = int(self.lbl_traffic.cget("text"))
        except:
            current_count = 0
                
        new_count = current_count + 1
        self.lbl_traffic.config(text=str(new_count))
        
        # One line. The helper handles the file logic.
        self.update_daily_json("", new_count)
    
    
    def open_edit_item_window(self):
        """
        Opens a popup to EDIT the selected item.
        FIX: Uses Row Index instead of Name lookup to handle duplicates correctly.
        """
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Select Item", "Please select an item to edit first.")
            return
        
        if not self.check_manager_override():
            return
        
        try:
            index = self.tree.index(selected_items[0])
            obj = self.inventory_objects[index]
        except (IndexError, ValueError):
            messagebox.showerror("Error", "Could not identify selected item.")
            return

        editor = tb.Toplevel(title=f"Edit: {obj.name}")
        editor.geometry("400x550")
        
        # Form
        tb.Label(editor, text="Edit Product Details", font=("Helvetica", 14, "bold")).pack(pady=10)
        
        entries = {}
        fields = [
            ("Name", obj.name),
            ("Vendor", obj.vendor),
            ("Size", obj.size),
            ("Style/Firmness", obj.attribute),
            ("SKU", obj.sku),
            ("Cost ($)", str(obj.cost)),
            ("Price ($)", str(obj.price)),
            ("Quantity", str(obj.count))
        ]
        
        for label, value in fields:
            row = tb.Frame(editor)
            row.pack(fill='x', padx=20, pady=5)
            tb.Label(row, text=label, width=15).pack(side='left')
            ent = tb.Entry(row)
            ent.pack(side='right', fill='x', expand=True)
            ent.insert(0, str(value))
            entries[label] = ent

        def save_changes():
            try:
                # 1. Gather Data into a clean dictionary
                updates = {
                    "name": entries["Name"].get(),
                    "vendor": entries["Vendor"].get(),
                    "size": entries["Size"].get(),
                    "attribute": entries["Style/Firmness"].get(),
                    "sku": entries["SKU"].get(),
                    "cost": float(entries["Cost ($)"].get()),
                    "price": float(entries["Price ($)"].get()),
                    "count": int(entries["Quantity"].get())
                }
                
                # 2. CLEAN REFACTOR: One line update
                self.db.update_table("inventory", updates, "id=?", (obj.id,))
                
                messagebox.showinfo("Saved", "Item updated!")
                self.load_initial_data()
                self.filter_search()
                editor.destroy()
                
            except ValueError:
                messagebox.showerror("Error", "Check your numbers.")

        tb.Button(editor, text="SAVE CHANGES", bootstyle="success", command=save_changes).pack(pady=20, fill='x', padx=20)


    def show_crew_report(self):
        log_file = self.paths['log_path'] 
        if not os.path.exists(log_file):
            messagebox.showinfo("Report", "No time logs found yet.")
            return
        with open(log_file, "r") as f:
            logs = json.load(f)
        totals = {}
        logs.sort(key=lambda x: (x['name'], datetime.strptime(x['time'], "%Y-%m-%d %H:%M:%S")))
        open_punches = {} 
        for entry in logs:
            name = entry['name']
            status = entry['status']
            time_obj = datetime.strptime(entry['time'], "%Y-%m-%d %H:%M:%S")
            if status == "IN":
                open_punches[name] = time_obj
            elif status == "OUT" and name in open_punches:
                start_time = open_punches.pop(name)
                duration = (time_obj - start_time).total_seconds()
                totals[name] = totals.get(name, 0) + duration

        report_text = "Weekly Hours Report:\n--------------------------\n"
        for name, seconds in totals.items():
            hours = seconds / 3600
            report_text += f"{name}: {hours:.2f} hrs\n"
        if open_punches:
            report_text += "\nCurrently Clocked In:\n"
            for name in open_punches:
                report_text += f"• {name}\n"
        messagebox.showinfo("Crew Hours", report_text)

    def get_json_val(self, date_key, suffix=""):
        """Helper to grab a specific value from the JSON for reports."""
        t_path = self.get_traffic_file_path()
        if os.path.exists(t_path):
            try:
                with open(t_path, 'r') as f:
                    data = json.load(f)
                    return data.get(f"{date_key}{suffix}", 0)
            except: return 0
        return 0


    def open_reports_dashboard(self):
        
        manual_deposit_val = self.deposit_entry.get().strip() or "0.00"
        self.update_daily_json("_deposit", manual_deposit_val)
        
        

        # --- 2. SETUP WINDOW ---
        dash = tb.Toplevel(title="Manager's Dashboard")
        dash.geometry("1380x850") 

        # --- 3. DYNAMIC MAPPING ---
        try:
            col_info = self.db.execute_manual_query("PRAGMA table_info(sales)")
            c_map = {info[1].lower(): i for i, info in enumerate(col_info)}
        except: c_map = {}

        def get_val(row, target_names, default=None):
            for name in target_names:
                if name.lower() in c_map:
                    idx = c_map[name.lower()]
                    if idx < len(row): return row[idx]
            return default

        # --- TABS ---
        tabs = tb.Notebook(dash, bootstyle="primary")
        tabs.pack(fill='both', expand=True, padx=10, pady=10)
        
        tab_month = tb.Frame(tabs)
        tab_day = tb.Frame(tabs)
        
        tabs.add(tab_month, text="Monthly Overview")
        tabs.add(tab_day, text="Daily Breakdown")

        # ==========================================
        # TAB 1: MONTHLY OVERVIEW
        # ==========================================
        m_foot = tb.Frame(tab_month, padding=10, bootstyle="secondary")
        m_foot.pack(side='bottom', fill='x')
        self.lbl_month_stats = tb.Label(m_foot, text="Loading...", font=("Helvetica", 12, "bold"), bootstyle="inverse-secondary")
        self.lbl_month_stats.pack()

        m_cols = ("day", "date", "sales", "tax", "total", "cost", "profit", "margin", "traffic", "sold", "ratio")
        m_tree = tb.Treeview(tab_month, columns=m_cols, show="headings", height=20, bootstyle="success")
        
        headers = {"day": "Day", "date": "Date", "sales": "Sales", "tax": "Tax", "total": "Total", "cost": "Cost", "profit": "Profit", "margin": "Margin", "traffic": "Walk-Ins", "sold": "Sold", "ratio": "Close %"}
        for c in m_cols:
            m_tree.heading(c, text=headers[c])
            m_tree.column(c, width=90, anchor='center')
        m_tree.column("day", width=50)
        
        m_scroll = tb.Scrollbar(tab_month, orient="vertical", command=m_tree.yview)
        m_tree.configure(yscrollcommand=m_scroll.set)
        m_tree.pack(side='left', fill='both', expand=True)
        m_scroll.pack(side='right', fill='y')

        # Load Data
        now = datetime.now()
        all_sales = self.db.select_data("sales") 
        days_data = {d: [] for d in range(1, 32)}
        
        if all_sales:
            for row in all_sales:
                try:
                    d_raw = get_val(row, ['date', 'timestamp'])
                    if not d_raw: continue
                    d_obj = None
                    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d", "%m-%d-%Y"):
                        try:
                            clean_date = str(d_raw).split(" ")[0]
                            d_obj = datetime.strptime(clean_date, fmt)
                            break
                        except: pass
                    if d_obj and d_obj.year == now.year and d_obj.month == now.month:
                        days_data[d_obj.day].append(row)
                except: continue

        run_sales = 0; run_profit = 0; run_traffic = 0; run_sold = 0
        m_tree.tag_configure('good', background='#2ecc71', foreground='white')
        
        num_days = calendar.monthrange(now.year, now.month)[1]
        
        for d in range(1, num_days + 1):
            day_rows = days_data.get(d, [])
            date_key = f"{now.year}-{now.month:02d}-{d:02d}"
            
            d_sales = 0; d_tax = 0; d_profit = 0; d_cost = 0
            unique_customers = set()
            
            for r in day_rows:
                try:
                    p = float(get_val(r, ['price', 'sale_price'], 0.0))
                    tr = float(get_val(r, ['tax_rate', 'tax'], 0.0))
                    prof = float(get_val(r, ['profit'], 0.0))
                    name = get_val(r, ['customer_name', 'customer', 'name'])
                    
                    d_sales += p
                    d_tax += (p * tr)
                    d_profit += prof
                    d_cost += (p - prof)
                    if name: unique_customers.add(name)
                except: continue

            d_sold_count = len(unique_customers) if d_sales > 0 else 0
            d_traffic = self.get_json_val(date_key, "")
            eff_traffic = max(d_traffic, d_sold_count) 
            d_ratio = (d_sold_count / eff_traffic * 100) if eff_traffic > 0 else 0.0

            d_total = d_sales + d_tax
            d_margin = (d_profit / d_sales * 100) if d_sales > 0 else 0
            
            if d <= now.day:
                val = (
                    datetime(now.year, now.month, d).strftime("%a"), d, 
                    f"${d_sales:,.0f}", f"${d_tax:,.0f}", f"${d_total:,.0f}",
                    f"${d_cost:,.0f}", f"${d_profit:,.0f}", 
                    f"{d_margin:.0f}%", 
                    eff_traffic, d_sold_count, f"{d_ratio:.0f}%"
                )
                tag = 'good' if d_sales > 0 else ''
                m_tree.insert('', 'end', values=val, tags=(tag,))
                run_sales += d_sales; run_profit += d_profit; run_traffic += eff_traffic; run_sold += d_sold_count

        month_ratio = (run_sold / run_traffic * 100) if run_traffic > 0 else 0
        self.lbl_month_stats.config(text=f"SALES: ${run_sales:,.2f}  |  PROFIT: ${run_profit:,.2f}  |  TRAFFIC: {run_traffic}  |  RATIO: {month_ratio:.1f}%")


        # ==========================================
        # TAB 2: DAILY BREAKDOWN (FIXED)
        # ==========================================
        # Columns: "margin" is now used instead of "gp" so it displays % in the row
        d_cols = ("cust", "sale", "tax", "total", "cost", "margin", "batch", "finance", "pay")
        d_tree = tb.Treeview(tab_day, columns=d_cols, show="headings", height=15)
        
        d_headers = {
            "cust": "Customer", "sale": "Sale", "tax": "Tax", "total": "Total", 
            "cost": "Cost", "margin": "Margin %", "batch": "Batch", 
            "finance": "Finance", "pay": "Method"
        }
        for c in d_cols:
            d_tree.heading(c, text=d_headers[c])
            d_tree.column(c, width=100, anchor='center')
        d_tree.column("cust", width=200, anchor='w')
        d_tree.pack(fill='both', expand=True, padx=10, pady=10)

        # Parse Today's Data
        today_rows = days_data.get(now.day, [])
        t_batch = 0; t_fin = 0; t_gp = 0 
        
        if today_rows:
            for r in today_rows:
                try:
                    name = get_val(r, ['customer_name', 'customer', 'name']) or "Guest"
                    price = float(get_val(r, ['price'], 0))
                    rate = float(get_val(r, ['tax_rate'], 0))
                    prof = float(get_val(r, ['profit'], 0))
                    
                   
                    m1 = str(get_val(r, ['pay_method'], "")).lower()
                    m2 = str(get_val(r, ['method'], "")).lower()
                    
                    method = m1 if (m1 and m1 not in ['none', 'null']) else m2
                    
                    t_gp += prof 
                    
                    tax = price * rate
                    total = price + tax
                    cost = price - prof
                    
                    # Row Calculation: Margin %
                    margin_pct = (prof / price * 100) if price > 0 else 0
                    
                    batch_val = 0; fin_val = 0
                    
                    # Bucketing Logic
                    combined = (m1 + " " + m2).lower()
                    if any(x in combined for x in ['card', 'visa', 'credit', 'debit', 'amex', 'disc']):
                        batch_val = total
                        t_batch += total
                    elif any(x in combined for x in ['syn', 'snap', 'fin', 'acima']):
                        fin_val = total
                        t_fin += total
                        
                    d_tree.insert('', 'end', values=(
                        name, f"${price:,.2f}", f"${tax:,.2f}", f"${total:,.2f}",
                        f"${cost:,.2f}", f"{margin_pct:.0f}%", # Row shows %
                        f"${batch_val:,.2f}" if batch_val else "-", 
                        f"${fin_val:,.2f}" if fin_val else "-",
                        method if (method and method != 'none') else "--"
                    ))
                except: continue

        # Footer
        d_foot = tb.Frame(tab_day, padding=15, bootstyle="dark")
        d_foot.pack(side='bottom', fill='x')
        try: final_dep = float(manual_deposit_val)
        except: final_dep = 0.00
        today_str = datetime.now().strftime("%Y-%m-%d")
        t_walkins = self.get_json_val(today_str, "")
        t_sold = len(set(get_val(r, ['customer_name']) for r in today_rows if get_val(r, ['customer_name'])))
        eff_t_walkins = max(t_walkins, t_sold)
        t_ratio = (t_sold / eff_t_walkins * 100) if eff_t_walkins > 0 else 0
        final_dep = self.get_json_val(today_str, "_deposit")
        tb.Label(d_foot, text=f"Traffic: {eff_t_walkins} | Sold: {t_sold} | Ratio: {t_ratio:.0f}%", font=("Helvetica", 12), bootstyle="inverse-dark").pack(side='left', padx=20)
        final_int_dep = float(final_dep)
        # Footer shows Total Profit $
        stats_lbl = f"TOTAL PROFIT: ${t_gp:,.2f}  |  Batch: ${t_batch:,.2f}  |  Fin: ${t_fin:,.2f}  |  DEPOSIT: ${final_int_dep:,.2f}"
        tb.Label(d_foot, text=stats_lbl, font=("Helvetica", 13, "bold"), bootstyle="warning").pack(side='right', padx=20)

    def check_manager_override(self):
        
        pin_input = simpledialog.askstring("Security Check", "Enter Manager PIN:", show='*', parent=self.app)
        
        if not pin_input:
            return False 

        
        for person in self.staff_list:
           
            if person.get('pin') == pin_input:
                if person.get('can_delete') == True:
                    return True
                else:
                    messagebox.showerror("Access Denied", f"{person['name']} is not authorized.")
                    return False
        
        messagebox.showerror("Invalid PIN", "PIN not found.")
        return False

    def show_cost_hover(self, event):
        """Reveals the Cost column when mouse is over the icon."""
        self.tree.column("cost", width=80, minwidth=80, stretch=False)
    
    def hide_cost_hover(self, event):
        """Hides the Cost column when mouse leaves."""
        self.tree.column("cost", width=0, minwidth=0, stretch=False)

    def peek_cost(self, event):
        """Shows cost when mouse enters"""
        self.tree.column("cost", width=80, stretch=True)

    def hide_cost(self, event):
        """Hides cost when mouse leaves"""
        self.tree.column("cost", width=0, stretch=False)

    def run(self):
        self.app.mainloop()

if __name__ == "__main__":
    user = sys.argv[1] if len(sys.argv) > 1 else "Guest"
    hub = SystemAxiomHub(logged_in_user='User')
    hub.run()
    


    
