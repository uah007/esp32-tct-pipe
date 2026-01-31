import os
import json
from config import SCRIPT_DIR

HISTORY_FILE = os.path.join(SCRIPT_DIR, "history.json")

class HistoryStore:
    def __init__(self):
        self.history = self.load()

    def load(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save(self, key, value):
        h = self.history.setdefault(key, [])
        if value in h:
            h.remove(value)
        h.insert(0, value)
        self.history[key] = h[:15]
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

    def get(self, key):
        return self.history.get(key, [])
