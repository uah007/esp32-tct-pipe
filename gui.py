import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import queue

from mqtt_manager import MQTTManager
from node_manager import NodeManager
from history_store import HistoryStore


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Node Bridge")

        self.log_queue = queue.Queue()

        # ===== Managers =====
        self.history_store = HistoryStore()
        self.node_manager = NodeManager(log_func=self.log)
        self.mqtt_manager = MQTTManager(
            log_func=self.log,
            history_store=self.history_store
        )
        self.mqtt_manager.set_node_manager(self.node_manager)

        # ===== UI =====
        self.fields = {}
        self._build_ui()

        self.root.after(100, self._update_console)

    # ================= UI =================

    def _build_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True)

        self.tab_main = tk.Frame(notebook)
        self.tab_mqtt = tk.Frame(notebook)

        notebook.add(self.tab_main, text="Main")
        notebook.add(self.tab_mqtt, text="MQTT")

        self._build_main_tab()
        self._build_mqtt_tab()

    def _field(self, parent, label, name, width):
        frame = tk.Frame(parent)
        frame.pack(fill="x", padx=5, pady=2)

        tk.Label(frame, text=label, width=10, anchor="w").pack(side="left")
        cb = ttk.Combobox(frame, width=width)
        cb.pack(side="left", fill="x", expand=True)

        values = self.history_store.get(name)
        cb["values"] = values
        if values:
            cb.set(values[0])

        self.fields[name] = cb
        return cb

    # ================= MAIN TAB =================

    def _build_main_tab(self):
        self.ip1_entry = self._field(self.tab_main, "IP1", "ip1", 20)
        self.port1_entry = self._field(self.tab_main, "Port1", "port1", 8)
        self.ip2_entry = self._field(self.tab_main, "IP2", "ip2", 20)
        self.port2_entry = self._field(self.tab_main, "Port2", "port2", 8)

        btn = tk.Button(
            self.tab_main,
            text="Send MQTT",
            command=self._on_send_mqtt
        )
        btn.pack(pady=5)

        self.console = ScrolledText(
            self.tab_main,
            height=15,
            state="disabled",
            font=("Consolas", 9)
        )
        self.console.pack(fill="both", expand=True, padx=5, pady=5)

    # ================= MQTT TAB =================

    def _build_mqtt_tab(self):
        self.broker_entry = self._field(self.tab_mqtt, "Broker", "mqtt_broker", 25)
        self.port_entry = self._field(self.tab_mqtt, "Port", "mqtt_port", 8)
        self.topic_entry = self._field(self.tab_mqtt, "Topic", "mqtt_topic", 25)
        self.user_entry = self._field(self.tab_mqtt, "Login", "mqtt_user", 15)
        self.pass_entry = self._field(self.tab_mqtt, "Password", "mqtt_pass", 15)

        btn = tk.Button(
            self.tab_mqtt,
            text="Apply / Reconnect",
            command=self._apply_mqtt_settings
        )
        btn.pack(pady=5)

    # ================= ACTIONS =================

    def _apply_mqtt_settings(self):
        broker = self.broker_entry.get().strip()
        port = self.port_entry.get().strip()
        topic = self.topic_entry.get().strip()
        user = self.user_entry.get().strip()
        password = self.pass_entry.get().strip()

        if not broker or not port or not topic:
            self.log("MQTT settings incomplete")
            return

        self.history_store.save("mqtt_broker", broker)
        self.history_store.save("mqtt_port", port)
        self.history_store.save("mqtt_topic", topic)
        self.history_store.save("mqtt_user", user)
        self.history_store.save("mqtt_pass", password)

        self.mqtt_manager.apply_settings(
            broker=broker,
            port=port,
            topic=topic,
            username=user,
            password=password
        )

    def _on_send_mqtt(self):
        ip1 = self.ip1_entry.get().strip()
        p1 = self.port1_entry.get().strip()
        ip2 = self.ip2_entry.get().strip()
        p2 = self.port2_entry.get().strip()

        if not all([ip1, p1, ip2, p2]):
            self.log("Main fields incomplete")
            return

        payload = f"{ip1},{p1},{ip2},{p2}"

        self.history_store.save("ip1", ip1)
        self.history_store.save("port1", p1)
        self.history_store.save("ip2", ip2)
        self.history_store.save("port2", p2)

        self.mqtt_manager.send_payload(payload)

    # ================= LOG =================

    def log(self, text):
        self.log_queue.put(text)

    def _update_console(self):
        try:
            while True:
                line = self.log_queue.get_nowait()
                self.console.config(state="normal")
                self.console.insert("end", line + "\n")
                self.console.see("end")
                self.console.config(state="disabled")
        except queue.Empty:
            pass

        self.root.after(100, self._update_console)
