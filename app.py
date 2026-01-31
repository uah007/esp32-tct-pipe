import subprocess
import threading
import os
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import queue
import paho.mqtt.client as mqtt
import json
import re
import tempfile
import time

# ================= НАСТРОЙКИ =================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(SCRIPT_DIR, "history.json")

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

WIN_X, WIN_Y, WIN_W, WIN_H = 1250, 50, 420, 450
DEFAULT_MQTT_PORT = 1883

# ================= УТИЛИТЫ =================

def kill_chrome_process(pid):
    try:
        subprocess.run(f"taskkill /F /PID {pid}", shell=True, check=True)
        time.sleep(1)
    except subprocess.CalledProcessError:
        pass

# ================= ПРИЛОЖЕНИЕ =================

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Node Bridge")
        self.root.geometry(f"{WIN_W}x{WIN_H}+{WIN_X}+{WIN_Y}")
        self.root.attributes("-topmost", True)

        self.chrome_proc = None
        self.chrome_profile = None
        self.node_proc = None
        self.wait_for_target = False

        self.log_queue = queue.Queue()
        self.chrome_processes = []
        self.is_chrome_open = False

        self.history = self.load_history()

        self.build_ui()
        self.mqtt = None  # MQTT создаётся при публикации или Apply

        self.root.after(100, self.update_console)

    # ================= UI =================

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
        tk.Button(btn_frame, text="MQTT", command=self.send_mqtt).pack(side="left")

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
        tk.Button(btns, text="Apply & Reconnect", command=self.apply_mqtt).pack(side="left")

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
            self.mqtt_port_entry.set(str(DEFAULT_MQTT_PORT))

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

    # ================= NODE =================

    def run_node(self):
        if self.node_proc and self.node_proc.poll() is None:
            self.log("Node.js уже запущен")
            return

        self.log("Запуск Node.js сервера")
        try:
            self.node_proc = subprocess.Popen(
                ["node", "server.js"],
                cwd=SCRIPT_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        except Exception as e:
            self.log(f"Node.js ERROR: {e}")
            return

        threading.Thread(target=self.read_node_output, daemon=True).start()

    def read_node_output(self):
        for line in self.node_proc.stdout:
            self.log(line.rstrip())
            clean = re.sub(r'\x1b\[[0-9;]*m', '', line)
            if "SERVER_READY" in clean:
                self.log("Node сервер готов → открываем Chrome")
                self.open_new_chrome()
            if self.wait_for_target and "Целевой IP подключён" in clean:
                self.wait_for_target = False
                self.open_new_chrome()

    # ================= CHROME =================

    def open_new_chrome(self):
        if self.is_chrome_open:
            return

        for proc in self.chrome_processes:
            if proc.poll() is None:
                kill_chrome_process(proc.pid)
        self.chrome_processes = []

        self.chrome_profile = tempfile.mkdtemp(prefix="chrome_profile_")
        ip = self.ip1_entry.get().strip() or "localhost"
        port = self.port1_entry.get().strip() or "9000"
        url = f"http://{ip}:{port}"

        proc = subprocess.Popen([
            CHROME_PATH,
            "--new-window",
            f"--user-data-dir={self.chrome_profile}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-extensions",
            url
        ])

        self.chrome_processes.append(proc)
        self.is_chrome_open = True
        self.log(f"Chrome открыт: {url}")
        threading.Timer(2.0, lambda: setattr(self, "is_chrome_open", False)).start()

    # ================= MQTT =================

    def create_mqtt_client(self):
        if self.mqtt:
            try:
                self.mqtt.loop_stop()
                self.mqtt.disconnect()
            except Exception:
                pass

        host = self.mqtt_host_entry.get().strip()
        port = int(self.mqtt_port_entry.get().strip() or DEFAULT_MQTT_PORT)
        user = self.mqtt_user_entry.get().strip()
        pwd = self.mqtt_pass_entry.get().strip()

        if not host:
            self.log("MQTT broker не задан, публикация невозможна")
            return None, None, None, None

        client = mqtt.Client()
        if user:
            client.username_pw_set(user, pwd)

        try:
            client.connect(host, port)
            threading.Thread(target=client.loop_forever, daemon=True).start()
            self.log(f"MQTT подключён: {host}:{port}")
        except Exception as e:
            self.log(f"MQTT ERROR: {e}")
            return None, None, None, None

        return client, host, port, user

    def apply_mqtt(self):
        self.mqtt, _, _, _ = self.create_mqtt_client()
        # Сохраняем историю
        for k in ["mqtt_host", "mqtt_port", "mqtt_user", "mqtt_pass"]:
            self.save_history(k, self.fields[k].get())

    def send_mqtt(self):
        topic = self.topic_entry.get().strip()
        ip1, p1 = self.ip1_entry.get().strip(), self.port1_entry.get().strip()
        ip2, p2 = self.ip2_entry.get().strip(), self.port2_entry.get().strip()
        payload = f"{ip1},{p1},{ip2},{p2}"

        if not all([ip1, p1, ip2, p2, topic]):
            self.log("Заполните все поля (IP, Port, Topic)")
            return

        # Берём актуальный MQTT клиент с вкладки
        self.mqtt, host, port, user = self.create_mqtt_client()
        if not self.mqtt:
            return

        confirmed = threading.Event()

        def on_temp_message(client, userdata, msg):
            try:
                if msg.payload.decode() == payload:
                    confirmed.set()
            except Exception:
                pass

        self.mqtt.message_callback_add(topic, on_temp_message)
        self.mqtt.subscribe(topic)

        try:
            self.mqtt.publish(topic, payload, retain=True)
        except Exception as e:
            self.log(f"MQTT send ERROR: {e}")
            self.mqtt.message_callback_remove(topic)
            return

        self.log("Ожидаем подтверждение публикации...")
        if not confirmed.wait(timeout=3):
            self.log("Нет подтверждения в топике, проверьте брокер или топик!")
            self.mqtt.message_callback_remove(topic)
            return

        self.log("Данные успешно опубликованы")
        self.mqtt.message_callback_remove(topic)

        # Сохраняем историю полей
        for k, v in [("ip1", ip1), ("port1", p1), ("ip2", ip2), ("port2", p2), ("topic", topic)]:
            self.save_history(k, v)

        self.wait_for_target = True
        if not self.node_proc or self.node_proc.poll() is not None:
            threading.Thread(target=self.run_node, daemon=True).start()
            self.log("Node.js сервер запущен после подтверждения MQTT")

    # ================= HISTORY =================

    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_history(self, key, value):
        h = self.history.setdefault(key, [])
        if value in h:
            h.remove(value)
        h.insert(0, value)
        self.history[key] = h[:15]
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

# ================= START =================

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
