import subprocess
import tempfile
import threading
import time
from utils import kill_chrome_process, check_if_chrome_is_running
from config import CHROME_PATH

class ChromeManager:
    def __init__(self, log_func):
        self.log = log_func
        self.chrome_proc = None
        self.chrome_profile = None
        self.chrome_processes = []
        self.is_chrome_open = False

    def open_new_chrome(self, url="http://localhost:9000"):
        if self.is_chrome_open:
            return

        try:
            # Создаем новый профиль
            self.chrome_profile = tempfile.mkdtemp(prefix="chrome_profile_")

            # Закрываем старые окна
            self.close_old_chrome_processes()

            # Запуск Chrome
            self.chrome_proc = subprocess.Popen([
                CHROME_PATH,
                "--new-window",
                f"--user-data-dir={self.chrome_profile}",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-extensions",
                url
            ])
            self.chrome_processes.append(self.chrome_proc)
            self.is_chrome_open = True
            self.log(f"Chrome открыт: {url}")

            threading.Timer(2.0, self.reset_lock).start()
        except Exception as e:
            self.log(f"Ошибка при открытии Chrome: {e}")

    def reset_lock(self):
        self.is_chrome_open = False

    def close_old_chrome_processes(self):
        for proc in self.chrome_processes:
            if proc.poll() is None:
                kill_chrome_process(proc.pid)
                self.log("Закрыто старое окно Chrome")
        self.chrome_processes = [p for p in self.chrome_processes if p.poll() is not None]
