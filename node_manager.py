import subprocess
import threading
import os


class NodeManager:
    def __init__(self, log_func=None):
        self.process = None
        self.thread = None
        self.log = log_func or (lambda msg: None)
        self.running = False

    def start(self):
        """
        Запускает Node.js сервер.
        Повторный запуск запрещён.
        """
        if self.running:
            self.log("Node.js сервер уже запущен")
            return

        server_path = os.path.join(os.getcwd(), "server.js")

        if not os.path.exists(server_path):
            self.log("server.js не найден")
            return

        try:
            self.log("Запуск Node.js сервера")

            self.process = subprocess.Popen(
                ["node", server_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1
            )

            self.running = True

            self.thread = threading.Thread(
                target=self._reader_loop,
                daemon=True
            )
            self.thread.start()

        except Exception as e:
            self.log(f"Ошибка запуска Node.js: {e}")
            self.running = False
            self.process = None

    def _reader_loop(self):
        """
        Читает stdout/stderr Node.js
        """
        try:
            while True:
                if not self.process:
                    break

                line = self.process.stdout.readline()
                if line:
                    line = line.rstrip()
                    self.log(line)

                err = self.process.stderr.readline()
                if err:
                    err = err.rstrip()
                    self.log(err)

                if self.process.poll() is not None:
                    break

        finally:
            code = None
            if self.process:
                code = self.process.poll()

            self.log(f"Node.js завершён (code={code})")
            self.process = None
            self.running = False

    def stop(self):
        """
        Корректная остановка Node.js
        """
        if not self.running or not self.process:
            return

        self.log("Остановка Node.js сервера")

        try:
            self.process.terminate()
            self.process.wait(timeout=3)
        except Exception:
            try:
                self.process.kill()
            except Exception:
                pass

        self.process = None
        self.running = False
