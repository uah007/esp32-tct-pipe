import paho.mqtt.client as mqtt
import threading
import time

class MQTTManager:
    def __init__(self, log_func, history_store):
        self.log = log_func
        self.history_store = history_store
        self.client = None
        self.connected = False
        self.current_config = None

    # ================= Connect =================
    def connect(self, config):
        self.current_config = config
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        if config.get("login") and config.get("password"):
            self.client.username_pw_set(config["login"], config["password"])

        try:
            self.client.connect(config["broker"], int(config["port"]))
            threading.Thread(target=self.client.loop_start, daemon=True).start()
            self.log(f"MQTT connecting to {config['broker']}:{config['port']} ...")
        except Exception as e:
            self.log(f"MQTT connection ERROR: {e}")

    def reconnect(self, config):
        if self.client:
            self.client.disconnect()
        self.connect(config)

    # ================= Publish =================
    def send(self, config, callback=None):
        self.connect(config)
        topic = config["topic"]
        payload = config.get("payload", "test")  # по умолчанию тест

        def wait_and_publish():
            # Ждём подключения
            t0 = time.time()
            while not self.connected:
                if time.time() - t0 > 5:
                    self.log("MQTT ERROR: Timeout waiting for connection")
                    return
                time.sleep(0.1)
            try:
                self.client.publish(topic, payload, retain=True)
                self.log(f"MQTT published to {topic}: {payload}")
                # Сохраняем историю
                for k in ["topic", "broker", "port", "login", "password"]:
                    if k in config:
                        self.history_store.save(k, config[k])
                if callback:
                    callback()
            except Exception as e:
                self.log(f"MQTT send ERROR: {e}")

        threading.Thread(target=wait_and_publish, daemon=True).start()

    # ================= Callbacks =================
    def on_connect(self, client, userdata, flags, rc):
        self.connected = True
        self.log(f"MQTT connected rc={rc}")
        topic = self.current_config.get("topic")
        if topic:
            client.subscribe(topic)

    def on_message(self, client, userdata, msg):
        self.log(f"MQTT received: {msg.payload.decode()}")
