import subprocess
import tempfile
import threading
from config import CHROME_PATH
from utils import kill_chrome_process, check_if_chrome_is_running

class ChromeManager:
    def __init__(self, log):
        self.log = log
        self.chrome_proc = None
        self.chrome_profile = None
        self.chrome_processes = []
        self.is_chrome_open = False

    def reset_lock(self):
        self.is_chrome_open = False

    def close_old(self):
        for proc in self.chrome_processes:
            if proc.poll() is None:
                kill_chrome_process(proc.pid)
                self.log("Закрыто старое окно Chrome")
        self.chrome_processes = [
            p for p in self.chrome_processes if p.poll() is not None
        ]

    def open(self, ip, port):
        if self.is_chrome_open:
            return

        if self.chrome_profile:
            if check_if_chrome_is_running(self.chrome_profile):
                self.log("Окно Chrome с этим профилем уже запущено, новое окно не будет открыто.")
                return

        self.close_old()

        self.chrome_profile = tempfile.mkdtemp(prefix="chrome_profile_")
        url = f"http://{ip}:{port}"

        try:
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
            self.log(f"Новое окно Chrome открыто с {url}")
            threading.Timer(2.0, self.reset_lock).start()
        except Exception as e:
            self.log(f"Ошибка при открытии Chrome: {e}")
