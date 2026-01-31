import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(SCRIPT_DIR, "history.json")

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

WIN_X, WIN_Y, WIN_W, WIN_H = 1250, 50, 400, 400

MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
