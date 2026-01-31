import subprocess
import threading
import re
from config import SCRIPT_DIR

class NodeManager:
    def __init__(self, log, on_target):
        self.log = log
        self.on_target = on_target
        self.proc = None

    def start(self):
        self.log("Запуск Node.js сервера")
        try:
            self.proc = subprocess.Popen(
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

        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for line in self.proc.stdout:
            clean = re.sub(r'\x1b\[[0-9;]*m', '', line.rstrip())
            self.log(clean)
            if "Целевой IP подключён" in clean:
                self.on_target()
