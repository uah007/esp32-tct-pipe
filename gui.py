import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from history_store import HistoryStore
from mqtt_manager import MQTTManager
from node_manager import NodeManager
from chrome_manager import ChromeManager
from config import WIN_X, WIN_Y, WIN_W, WIN_H

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Node Bridge")
        self.root.geometry(f"{WIN_W}x{WIN_H}+{WIN_X}+{WIN_Y}")
        self.root.attributes("-topmost", True)

        # ================= Managers =================
        self.history_store = HistoryStore()
        self.mqtt_manager = MQTTManager(log_func=self.log, history_store=self.history_store)
        self.node_manager = NodeManager(log_func=self.log)
        self.chrome_manager = ChromeManager(log_func=self.log)

        # ================= State =================
        self.wait_for_target = False

        # ================= Fields Dict =================
        self.fields = {}  # Создаём один раз здесь, до build_ui()

        # ================= UI =================
        self.build_ui()

        # ================= Start Console Update =================
        self.log_queue = []
        self.root.after(100, self.update_console)

    # ================= UI =================
    def build_ui(self):
        self.tabs = ttk.Notebook(self.root)
        self.tab_main = ttk.Frame(self.tabs)
        self.tab_mqtt = ttk.Frame(self.tabs)
        self.tabs.add(self.tab_main, text="Main")
        self.tabs.add(self.tab_mqtt, text="MQTT")
        self.tabs.pack(fill="both", expand=True)

        # ------------------ Main Tab ------------------
        f0 = tk.Frame(self.tab_main); f0.pack(fill="x", padx=5, pady=2)
        self.ip1_entry = self._field(f0, "IP1", "ip1", 15)
        self.port1_entry = self._field(f0, "Port1", "port1", 6)

        f1 = tk.Frame(self.tab_main); f1.pack(fill="x", padx=5, pady=2)
        self.ip2_entry = self._field(f1, "IP2", "ip2", 15)
        self.port2_entry = self._field(f1, "Port2", "port2", 6)

        bf = tk.Frame(self.tab_main); bf.pack(fill="x", padx=5, pady=5)
        tk.Button(bf, text="Send MQTT", command=self.send_mqtt).pack(side="left")
        tk.Button(bf, text="Apply/Reconnect", command=self.apply_mqtt).pack(side="left")

        self.console = ScrolledText(self.tab_main, font=("Consolas", 9))
        self.console.pack(fill="both", expand=True, padx=5, pady=5)
        self.console.config(state="disabled")

        # ------------------ MQTT Tab ------------------
        f2 = tk.Frame(self.tab_mqtt); f2.pack(fill="x", padx=5, pady=2)
        self.topic_entry = self._field(f2, "Topic", "topic", 20)

        f3 = tk.Frame(self.tab_mqtt); f3.pack(fill="x", padx=5, pady=2)
        self.broker_entry = self._field(f3, "Broker", "broker", 20)
        self.port_entry = self._field(f3, "Port", "port", 6)
        self.login_entry = self._field(f3, "Login", "login", 10)
        self.pass_entry = self._field(f3, "Password", "password", 10)

    def _field(self, frame, label, name, width):
        tk.Label(frame, text=label).pack(side="left")
        cb = ttk.Combobox(frame, width=width, values=self.history_store.get(name))
        cb.pack(side="left", padx=2)
        # Подтягиваем последнее значение из истории
        if self.history_store.get(name):
            cb.set(self.history_store.get(name)[0])
        self.fields[name] = cb
        return cb

    # ================= LOG =================
    def log(self, text):
        self.log_queue.append(text)

    def update_console(self):
        if self.log_queue:
            self.console.config(state="normal")
            for line in self.log_queue:
                self.console.insert("end", line + "\n")
                self.console.see("end")
            self.console.config(state="disabled")
            self.log_queue.clear()
        self.root.after(100, self.update_console)

    # ================= MQTT =================
    def send_mqtt(self):
        # Берем последние значения с вкладки MQTT
        config = {
            "topic": self.topic_entry.get().strip(),
            "broker": self.broker_entry.get().strip(),
            "port": self.port_entry.get().strip(),
            "login": self.login_entry.get().strip(),
            "password": self.pass_entry.get().strip(),
            # Для payload используем IP1/IP2 и порты
            "payload": f"{self.ip1_entry.get().strip()},{self.port1_entry.get().strip()},{self.ip2_entry.get().strip()},{self.port2_entry.get().strip()}"
        }

        if not all([config["topic"], config["broker"], config["port"]]):
            self.log("Заполните поля Topic, Broker и Port")
            return

        # Отправка через MQTTManager
        def after_send():
            self.node_manager.wait_for_target = True
            self.node_manager.run_node()
            self.chrome_manager.open_new_chrome(f"http://{self.ip1_entry.get().strip()}:{self.port1_entry.get().strip()}")

        self.mqtt_manager.send(config, callback=after_send)

    def apply_mqtt(self):
        # Apply/Reconnect MQTT с новыми настройками
        config = {
            "topic": self.topic_entry.get().strip(),
            "broker": self.broker_entry.get().strip(),
            "port": self.port_entry.get().strip(),
            "login": self.login_entry.get().strip(),
            "password": self.pass_entry.get().strip()
        }
        self.mqtt_manager.reconnect(config)
