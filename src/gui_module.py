import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import queue
import sys
import os

# ================= GUI MODULE =================

def resource_path(relative_path):
    """Получить абсолютный путь к ресурсу, работает для dev и для PyInstaller"""
    try:
        # PyInstaller создает временную папку и сохраняет путь в _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class AppGUI:
    def __init__(self, root, history, callbacks):
        self.root = root
        self.history = history
        self.callbacks = callbacks
        self.log_queue = queue.Queue()
        
        self.root.title("Node Bridge")
        self.root.geometry(f"{callbacks['WIN_W']}x{callbacks['WIN_H']}+{callbacks['WIN_X']}+{callbacks['WIN_Y']}")
        self.root.attributes("-topmost", True)
        
        self.build_ui()
        self.root.after(100, self.update_console)

    def build_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True)

        tab_main = tk.Frame(notebook)
        tab_mqtt = tk.Frame(notebook)

        notebook.add(tab_main, text="Основное")
        notebook.add(tab_mqtt, text="MQTT")

        def field(parent, label, name, width, show=None):
            frame = tk.Frame(parent)
            frame.pack(fill="x", padx=6, pady=3)
            tk.Label(frame, text=label, width=12, anchor="w").pack(side="left")
            cb = ttk.Combobox(frame, width=width, values=self.history.get(name, []))
            if show:
                cb.configure(show=show)
            cb.pack(side="left", fill="x", expand=True)
            if self.history.get(name):
                cb.set(self.history[name][0])
            return cb

        # ---------- Основное ----------
        self.ip1_entry = field(tab_main, "IP1", "ip1", 22)
        self.port1_entry = field(tab_main, "Port1", "port1", 8)
        self.ip2_entry = field(tab_main, "IP2", "ip2", 22)
        self.port2_entry = field(tab_main, "Port2", "port2", 8)

        btn_frame = tk.Frame(tab_main)
        btn_frame.pack(fill="x", padx=6, pady=6)
        tk.Button(btn_frame, text="MQTT", command=self.callbacks['send_mqtt']).pack(side="left")

        self.console = ScrolledText(tab_main, font=("Consolas", 9))
        self.console.pack(fill="both", expand=True, padx=6, pady=6)
        self.console.config(state="disabled")

        # ---------- MQTT ----------
        self.topic_entry = field(tab_mqtt, "Topic", "topic", 30)
        self.mqtt_host_entry = field(tab_mqtt, "Broker", "mqtt_host", 30)
        self.mqtt_port_entry = field(tab_mqtt, "Port", "mqtt_port", 8)
        self.mqtt_user_entry = field(tab_mqtt, "Login", "mqtt_user", 25)
        self.mqtt_pass_entry = field(tab_mqtt, "Password", "mqtt_pass", 25, show="*")

        btns = tk.Frame(tab_mqtt)
        btns.pack(fill="x", padx=6, pady=8)
        tk.Button(btns, text="Apply & Reconnect", command=self.callbacks['apply_mqtt']).pack(side="left")

        self.fields = {
            "topic": self.topic_entry,
            "ip1": self.ip1_entry,
            "port1": self.port1_entry,
            "ip2": self.ip2_entry,
            "port2": self.port2_entry,
            "mqtt_host": self.mqtt_host_entry,
            "mqtt_port": self.mqtt_port_entry,
            "mqtt_user": self.mqtt_user_entry,
            "mqtt_pass": self.mqtt_pass_entry,
        }

        if not self.mqtt_port_entry.get():
            self.mqtt_port_entry.set(str(self.callbacks['DEFAULT_MQTT_PORT']))

    # ================= ЛОГ =================

    def log(self, text):
        self.log_queue.put(text)

    def update_console(self):
        try:
            while True:
                line = self.log_queue.get_nowait()
                self.console.config(state="normal")
                self.console.insert("end", line + "\n")
                self.console.see("end")
                self.console.config(state="disabled")
        except queue.Empty:
            pass
        self.root.after(100, self.update_console)
