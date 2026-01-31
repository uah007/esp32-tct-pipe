import subprocess
import threading
import os
import tkinter as tk
import json
import re
import tempfile
import time
from gui_module import AppGUI
from mqtt_module import MQTTHandler

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

        self.chrome_proc = None
        self.chrome_profile = None
        self.node_proc = None
        self.wait_for_target = False

        self.chrome_processes = []
        self.is_chrome_open = False

        self.history = self.load_history()

        # Создаём MQTT handler
        self.mqtt_handler = MQTTHandler(self.log, DEFAULT_MQTT_PORT)

        # Создаём GUI с callbacks
        callbacks = {
            'send_mqtt': self.send_mqtt,
            'apply_mqtt': self.apply_mqtt,
            'WIN_X': WIN_X,
            'WIN_Y': WIN_Y,
            'WIN_W': WIN_W,
            'WIN_H': WIN_H,
            'DEFAULT_MQTT_PORT': DEFAULT_MQTT_PORT
        }
        self.gui = AppGUI(root, self.history, callbacks)

    # ================= ЛОГ =================

    def log(self, text):
        self.gui.log(text)

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
        ip = self.gui.ip1_entry.get().strip() or "localhost"
        port = self.gui.port1_entry.get().strip() or "9000"
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

    def apply_mqtt(self):
        host = self.gui.mqtt_host_entry.get().strip()
        port = self.gui.mqtt_port_entry.get().strip()
        user = self.gui.mqtt_user_entry.get().strip()
        pwd = self.gui.mqtt_pass_entry.get().strip()
        
        self.mqtt_handler.apply_mqtt(host, port, user, pwd)
        
        # Сохраняем историю
        for k in ["mqtt_host", "mqtt_port", "mqtt_user", "mqtt_pass"]:
            self.save_history(k, self.gui.fields[k].get())

    def send_mqtt(self):
        topic = self.gui.topic_entry.get().strip()
        ip1, p1 = self.gui.ip1_entry.get().strip(), self.gui.port1_entry.get().strip()
        ip2, p2 = self.gui.ip2_entry.get().strip(), self.gui.port2_entry.get().strip()
        payload = f"{ip1},{p1},{ip2},{p2}"

        if not all([ip1, p1, ip2, p2, topic]):
            self.log("Заполните все поля (IP, Port, Topic)")
            return

        # Берём актуальный MQTT клиент с вкладки
        host = self.gui.mqtt_host_entry.get().strip()
        port = self.gui.mqtt_port_entry.get().strip()
        user = self.gui.mqtt_user_entry.get().strip()
        pwd = self.gui.mqtt_pass_entry.get().strip()
        
        success = self.mqtt_handler.send_mqtt(topic, payload, host, port, user, pwd)
        if not success:
            return

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
