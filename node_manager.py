import subprocess
import threading
import os
import re
from config import SCRIPT_DIR

class NodeManager:
    def __init__(self, log_func):
        self.log = log_func
        self.node_proc = None
        self.wait_for_target = False

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
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            threading.Thread(target=self.read_output, daemon=True).start()
        except Exception as e:
            self.log(f"Node.js ERROR: {e}")

    def read_output(self):
        for line in self.node_proc.stdout:
            self.log(line.rstrip())
            clean = re.sub(r'\x1b\[[0-9;]*m', '', line)
            if self.wait_for_target and "Целевой IP подключён" in clean:
                self.wait_for_target = False
                self.log("Node trigger → открыть новое окно Chrome")
