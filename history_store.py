import json
import os
from config import HISTORY_FILE

class HistoryStore:
    def load(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def save(self, history):
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    def save_unique(self, history, key, value):
        if value not in history.get(key, []):
            history.setdefault(key, []).insert(0, value)

    def push(self, history, key, value):
        h = history.setdefault(key, [])
        if value in h:
            h.remove(value)
        h.insert(0, value)
        history[key] = h[:15]
        self.save(history)
