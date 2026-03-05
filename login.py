import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox
import json
import os
import subprocess

# --- SETUP PATHS ---
# This ensures it looks in your ignored wharehouse_data folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROSTER_PATH = os.path.join(BASE_DIR, "wharehouse_data", "roster.json")

def launch_pos(username):
    """Sets environment and starts the main POS."""
    os.environ['CURRENT_USER'] = username
    # This calls your big main.py file
    subprocess.Popen(["python", "main.py"])
    root.destroy()

def check_login():
    """Verifies PIN against the local roster.json."""
    pin = pin_entry.get()
    try:
        with open(ROSTER_PATH, "r") as f:
            data = json.load(f)
            for user in data.get('associates', []):
                if user.get('pin') == pin:
                    launch_pos(user['name'])
                    return
            messagebox.showerror("Error", "Invalid PIN")
    except Exception as e:
        messagebox.showerror("Error", f"Could not load roster: {e}")

class PinApp:
    """The 'Staff Manager' window that everyone can use to change PINs."""
    def __init__(self, master):
        self.win = tb.Toplevel(master)
        self.win.title("PIN Manager")
        self.win.geometry("350x300")
        
        tb.Label(self.win, text="Change Staff PIN", font=("Helvetica", 14, "bold")).pack(pady=10)
        
        self.name_var = tb.StringVar()
        self.pin_var = tb.StringVar()

        tb.Label(self.win, text="Enter Your Name:").pack()
        tb.Entry(self.win, textvariable=self.name_var).pack(pady=5, padx=20, fill='x')
        
        tb.Label(self.win, text="New 4-Digit PIN:").pack()
        self.pin_entry = tb.Entry(self.win, textvariable=self.pin_var, show="*")
        self.pin_entry.pack(pady=5, padx=20, fill='x')
        
        tb.Button(self.win, text="SAVE NEW PIN", bootstyle=SUCCESS, command=self.save_pin).pack(pady=20)

    def save_pin(self):
        name = self.name_var.get().strip()
        new_pin = self.pin_var.get().strip()
        
        if len(new_pin) != 4 or not new_pin.isdigit():
            messagebox.showerror("Error", "PIN must be 4 digits.")
            return

        try:
            with open(ROSTER_PATH, "r") as f:
                data = json.load(f)
            
            updated = False
            for user in data['associates']:
                if user['name'].lower() == name.lower():
                    user['pin'] = new_pin
                    updated = True
                    break
            
            if updated:
                with open(ROSTER_PATH, "w") as f:
                    json.dump(data, f, indent=4)
                messagebox.showinfo("Success", f"PIN updated for {name}")
                self.win.destroy()
            else:
                messagebox.showerror("Error", "Name not found.")
        except Exception as e:
            messagebox.showerror("Error", f"Save failed: {e}")

# --- MAIN LOGIN UI ---
root = tb.Window(themename="cyborg", size=(350, 400))
root.title("Axiom Security")

tb.Label(root, text="System Axiom", font=("Helvetica", 18, "bold"), bootstyle=INFO).pack(pady=20)

pin_entry = tb.Entry(root, show="*", justify="center", font=("Helvetica", 20))
pin_entry.pack(pady=10, padx=40)
pin_entry.bind("<Return>", lambda e: check_login())

tb.Button(root, text="LOGIN", command=check_login, bootstyle=SUCCESS, width=15).pack(pady=15)

# This is the link to the PinApp class
tb.Button(root, text="Change My PIN", command=lambda: PinApp(root), bootstyle="link-secondary").pack(side='bottom', pady=10)

root.mainloop()