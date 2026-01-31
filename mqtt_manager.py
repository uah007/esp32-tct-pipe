import threading
import paho.mqtt.client as mqtt


class MQTTManager:
    def __init__(self, log, on_message):
        self.log = log
        self.on_message_cb = on_message

        self.client = None
        self.thread = None

        self.broker = None
        self.port = None
        self.username = None
        self.password = None
        self.topic = None

    # ---------- lifecycle ----------

    def configure(self, broker, port, username=None, password=None):
        self.broker = broker
        self.port = int(port) if str(port).isdigit() else 1883
        self.username = username or None
        self.password = password or None

    def connect(self, topic=None):
        self.disconnect()

        self.topic = topic

        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

        if self.username:
            self.client.username_pw_set(self.username, self.password)

        try:
            self.client.connect(self.broker, self.port)
        except Exception as e:
            self.log(f"MQTT connect ERROR: {e}")
            return

        self.thread = threading.Thread(
            target=self.client.loop_forever,
            daemon=True
        )
        self.thread.start()

        self.log(f"MQTT connecting to {self.broker}:{self.port}")

    def disconnect(self):
        try:
            if self.client:
                self.client.disconnect()
        except Exception:
            pass
        self.client = None

    # ---------- api ----------

    def publish(self, topic, payload):
        if not self.client:
            self.log("MQTT not connected")
            return
        self.client.publish(topic, payload, retain=True)

    # ---------- callbacks ----------

    def _on_connect(self, client, userdata, flags, rc):
        self.log(f"MQTT connected rc={rc}")
        if self.topic:
            client.subscribe(self.topic)

    def _on_message(self, client, userdata, msg):
        self.on_message_cb(msg.payload.decode())
