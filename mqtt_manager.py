import threading
import paho.mqtt.client as mqtt


class MQTTManager:
    def __init__(self, log_func, history_store, node_manager=None):
        self.log = log_func
        self.history = history_store
        self.node_manager = node_manager

        self.client = None
        self.connected = False

        self.broker = ""
        self.port = 1883
        self.topic = ""

        self.username = None
        self.password = None

    # ================= DEPENDENCIES =================

    def set_node_manager(self, node_manager):
        self.node_manager = node_manager

    # ================= CONNECTION =================

    def apply_settings(self, broker, port, topic, username=None, password=None):
        self.broker = broker
        self.port = int(port)
        self.topic = topic
        self.username = username or None
        self.password = password or None

        self._connect()

    def _connect(self):
        if self.client:
            try:
                self.client.disconnect()
            except Exception:
                pass

        self.client = mqtt.Client()

        if self.username:
            self.client.username_pw_set(self.username, self.password)

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

        self.log(f"MQTT connecting to {self.broker}:{self.port} ...")

        try:
            self.client.connect(self.broker, self.port, keepalive=30)
        except Exception as e:
            self.log(f"MQTT connection ERROR: {e}")
            return

        threading.Thread(
            target=self.client.loop_forever,
            daemon=True
        ).start()

    # ================= CALLBACKS =================

    def _on_connect(self, client, userdata, flags, rc):
        self.connected = (rc == 0)
        self.log(f"MQTT connected rc={rc}")

        if self.connected and self.topic:
            client.subscribe(self.topic)

    def _on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode()
            self.log(f"MQTT received: {payload}")
        except Exception:
            pass

    # ================= SEND =================

    def send_payload(self, payload):
        """
        1. Публикуем MQTT
        2. После публикации запускаем Node.js (если он привязан)
        """

        if not self.connected:
            self.log("MQTT not connected")
            return

        if not self.topic:
            self.log("MQTT topic is empty")
            return

        self.client.publish(self.topic, payload, retain=True)
        self.log(f"MQTT published to {self.topic}: {payload}")

        if self.node_manager:
            self.node_manager.start()
        else:
            self.log("NodeManager not attached — Node.js не запущен")
