import os

# ================= SCRIPT PATH =================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ================= CHROME =================
# Путь к Chrome. Укажи свой, если другой
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# ================= WINDOW =================
WIN_X, WIN_Y = 1250, 50
WIN_W, WIN_H = 400, 400

# ================= MQTT DEFAULTS =================
DEFAULT_MQTT_BROKER = ""  # оставляем пустым, пользователь вводит
DEFAULT_MQTT_PORT = 1883

# ================= NODE =================
DEFAULT_NODE_PORT = 9000  # Порт для TCP-сервера Node.js
