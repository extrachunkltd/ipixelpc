import tkinter as tk
from tkinter import filedialog, messagebox
import threading
from bleak import BleakScanner
import pypixelcolor
import os

class PixelApp:
    def __init__(self, root):
        self.root = root
        self.root.title("iPixel BLE Controller")
        self.root.geometry("500x600")
        
        self.path = None

        # --- UI ---
        tk.Label(root, text="Step 1: Discover Device", font=("Arial", 12, "bold")).pack(pady=5)
        self.btn_scan = tk.Button(root, text="Scan Bluetooth", command=self.start_scan)
        self.btn_scan.pack(fill="x", padx=40)
        
        self.device_list = tk.Listbox(root, height=5)
        self.device_list.pack(fill="x", padx=40, pady=5)

        tk.Label(root, text="Step 2: Select Image", font=("Arial", 12, "bold")).pack(pady=10)
        self.btn_select = tk.Button(root, text="Choose File", command=self.load_image)
        self.btn_select.pack()

        self.status_label = tk.Label(root, text="Status: Ready", fg="blue")
        self.status_label.pack(pady=5)

        self.btn_send = tk.Button(root, text="UPLOAD TO DEVICE", command=self.start_upload, 
                                  bg="#2ecc71", fg="white", font=("Arial", 12, "bold"), height=2)
        self.btn_send.pack(fill="x", padx=40, pady=20)

    def start_scan(self):
        self.status_label.config(text="Scanning...", fg="orange")
        self.device_list.delete(0, tk.END)
        threading.Thread(target=self.run_scan, daemon=True).start()

    def run_scan(self):
        import asyncio
        async def scan(): return await BleakScanner.discover()
        loop = asyncio.new_event_loop()
        found = loop.run_until_complete(scan())
        for d in found:
            name = d.name if d.name else "Unknown"
            self.device_list.insert(tk.END, f"{d.address} | {name}")
        self.root.after(0, lambda: self.status_label.config(text="Scan Finished", fg="green"))

    def load_image(self):
        # We store the string path here
        self.path = filedialog.askopenfilename()
        if self.path:
            self.status_label.config(text=f"Selected: {os.path.basename(self.path)}", fg="green")

    def start_upload(self):
        selection = self.device_list.curselection()
        if not (selection and self.path):
            messagebox.showwarning("Warning", "Select device AND image!")
            return
        addr = self.device_list.get(selection[0]).split(" | ")[0]
        threading.Thread(target=self.do_upload, args=(addr,), daemon=True).start()

    def do_upload(self, addr):
        try:
            # 1. Initialize Client
            client = pypixelcolor.Client(addr)
            client.connect()
            
            # 2. Status Update
            self.root.after(0, lambda: self.status_label.config(text="Uploading file path...", fg="orange"))
            
            # 3. THE FIX: Pass the STRING path, not the PIL Image object
            # The library likely calls "if path.exists():" inside this method
            client.send_image(self.path)
            
            client.disconnect()
            self.root.after(0, lambda: self.status_label.config(text="UPLOAD SUCCESSFUL!", fg="green"))
            
        except Exception as e:
            print(f"Error: {e}")
            self.root.after(0, lambda: self.status_label.config(text="Upload Failed", fg="red"))

if __name__ == "__main__":
    root = tk.Tk()
    app = PixelApp(root)
    root.mainloop()