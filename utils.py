"""
================================================================================
MODULE: System Axiom Utilities (utils.py)
PROJECT: System Axiom POS
AUTHOR: [Your Name/Brand Name]
DESCRIPTION:
    Support utilities for the System Axiom POS interface, including 
    branding animations, splash screen transitions, and UI helper functions.

FUNCTIONS:
    - run_splash: Handles the asynchronous fade-in and display of brand assets.
    - [Other function names as you add them]

DEPENDENCIES:
    - ttkbootstrap for themed windowing.
    - Pillow (PIL) for advanced image rendering on Linux/Windows.
================================================================================
"""

import ttkbootstrap as tb
from PIL import Image, ImageTk
import os
import time

def run_splash(root, image_path, display_time=2500):
    if not image_path or not os.path.exists(image_path):
        print(f"⚠️ Splash skipped: Image not found at {image_path}")
        return 

    # 1. Create the Toplevel window
    splash = tb.Toplevel(root)
    splash.overrideredirect(True)
    splash.attributes("-alpha", 0.0)
    splash.attributes("-topmost", True)

    try:
        # 2. Load Image
        pil_img = Image.open(image_path)
        img_tk = ImageTk.PhotoImage(pil_img)
        
        img_w, img_h = pil_img.size
        screen_w = splash.winfo_screenwidth()
        screen_h = splash.winfo_screenheight()
        x = (screen_w // 2) - (img_w // 2)
        y = (screen_h // 2) - (img_h // 2)
        splash.geometry(f"{img_w}x{img_h}+{x}+{y}")

        label = tb.Label(splash, image=img_tk)
        label.image = img_tk 
        label.pack()

        # 3. The Visual Fade-In (Fast Loop)
        alpha = 0.0
        while alpha < 1.0:
            alpha += 0.1
            splash.attributes("-alpha", alpha)
            splash.update()
            time.sleep(0.02)

        # 4. THE HANDOFF: This stops the 'pkill' issues
        # We tell the window to quit the loop after the display time
        splash.after(display_time, splash.quit)
        
        # We start the loop here. Python stays on this line until 'quit' is called.
        splash.mainloop()

        # 5. Cleanup after the loop finishes
        splash.destroy()

    except Exception as e:
        print(f"❌ Splash error: {e}")
        # If anything fails, try to kill the splash so the main app can still run
        try:
            splash.destroy()
        except:
            pass