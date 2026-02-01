import subprocess
import threading
import os
import tkinter as tk
import json
import re
import tempfile
import time
import sys
import shutil
import atexit
from gui_module import AppGUI
from mqtt_module import MQTTHandler

# ================= НАСТРОЙКИ =================

def get_app_dir():
    """Получить директорию приложения (для сохранения данных)"""
    if getattr(sys, 'frozen', False):
        # Если запущено как EXE, сохраняем данные рядом с EXE
        return os.path.dirname(sys.executable)
    else:
        # Если запущено как скрипт
        return os.path.dirname(os.path.abspath(__file__))

def resource_path(relative_path):
    """Получить абсолютный путь к ресурсу (для встроенных файлов)"""
    try:
        # PyInstaller создает временную папку и сохраняет путь в _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

SCRIPT_DIR = get_app_dir()
HISTORY_FILE = os.path.join(SCRIPT_DIR, "history.json")

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

WIN_X, WIN_Y, WIN_W, WIN_H = 1250, 50, 420, 450
DEFAULT_MQTT_PORT = 1883

# ================= УТИЛИТЫ =================

def kill_chrome_process(pid):
    try:
        subprocess.run(f"taskkill /F /PID {pid}", shell=True, check=True,
                      creationflags=subprocess.CREATE_NO_WINDOW)
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
        
        # Список временных директорий для очистки
        self.temp_dirs = []

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
        
        # Регистрируем очистку при выходе
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        atexit.register(self.cleanup)

    # ================= ЛОГ =================

    def log(self, text):
        self.gui.log(text)

    # ================= NODE =================

    def run_node(self):
        if self.node_proc and self.node_proc.poll() is None:
            self.log("Node.js уже запущен")
            return

        self.log("Запуск Node.js сервера")
        
        # Определяем путь к Node.js
        if getattr(sys, 'frozen', False):
            # Если запущено как EXE, используем встроенный Node.js
            node_exe = resource_path(os.path.join('nodejs', 'node.exe'))
            server_js_path = resource_path('server.js')
        else:
            # Если запущено как скрипт, используем системный Node.js
            node_exe = 'node'
            # Ищем server.js в корне проекта (на уровень выше src)
            project_root = os.path.dirname(SCRIPT_DIR)
            server_js_path = os.path.join(project_root, "server.js")
            
            # Если не найден в корне, ищем рядом со скриптом (обратная совместимость)
            if not os.path.exists(server_js_path):
                server_js_path = os.path.join(SCRIPT_DIR, "server.js")
        
        if not os.path.exists(server_js_path):
            self.log(f"ERROR: server.js не найден: {server_js_path}")
            return
        
        try:
            # Для EXE используем полный путь к node.exe
            if getattr(sys, 'frozen', False):
                if not os.path.exists(node_exe):
                    self.log(f"ERROR: Node.js не найден: {node_exe}")
                    self.log("ВНИМАНИЕ: Node.js не был встроен в EXE при сборке!")
                    return
                
                self.node_proc = subprocess.Popen(
                    [node_exe, server_js_path],
                    cwd=os.path.dirname(server_js_path),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    bufsize=1,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                # Для разработки используем системный node
                self.node_proc = subprocess.Popen(
                    [node_exe, server_js_path],
                    cwd=os.path.dirname(server_js_path),  # Используем директорию где находится server.js
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
        self.temp_dirs.append(self.chrome_profile)  # Добавляем в список для очистки
        
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
        ], creationflags=subprocess.CREATE_NO_WINDOW)

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
        # Закрываем Chrome сразу при нажатии кнопки
        for proc in self.chrome_processes:
            if proc.poll() is None:
                kill_chrome_process(proc.pid)
        self.chrome_processes = []
        self.is_chrome_open = False
        self.log("Chrome закрыт")
        
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

        # Если Node.js уже запущен, открываем Chrome сразу
        if self.node_proc and self.node_proc.poll() is None:
            self.log("MQTT отправлен → открываем Chrome")
            self.open_new_chrome()
        else:
            # Если Node.js не запущен, запускаем его и ждём сигнала
            self.wait_for_target = True
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
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log(f"Ошибка сохранения истории: {e}")
    
    # ================= CLEANUP =================
    
    def cleanup(self):
        """Очистка ресурсов при выходе"""
        # Закрываем Chrome процессы
        for proc in self.chrome_processes:
            try:
                if proc.poll() is None:
                    proc.terminate()
                    proc.wait(timeout=2)
            except Exception:
                pass
        
        # Закрываем Node.js
        if self.node_proc and self.node_proc.poll() is None:
            try:
                self.node_proc.terminate()
                self.node_proc.wait(timeout=2)
            except Exception:
                pass
        
        # Удаляем временные директории
        for temp_dir in self.temp_dirs:
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass
    
    def on_closing(self):
        """Обработчик закрытия окна"""
        self.cleanup()
        self.root.destroy()

# ================= START =================

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
