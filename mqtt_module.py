import paho.mqtt.client as mqtt
import threading

# ================= MQTT MODULE =================

class MQTTHandler:
    def __init__(self, log_callback, default_port):
        self.log_callback = log_callback
        self.default_port = default_port
        self.mqtt = None

    def create_mqtt_client(self, host, port, user, pwd):
        if self.mqtt:
            try:
                self.mqtt.loop_stop()
                self.mqtt.disconnect()
            except Exception:
                pass

        port = int(port or self.default_port)

        if not host:
            self.log_callback("MQTT broker не задан, публикация невозможна")
            return None, None, None, None

        client = mqtt.Client()
        if user:
            client.username_pw_set(user, pwd)

        try:
            client.connect(host, port)
            threading.Thread(target=client.loop_forever, daemon=True).start()
            self.log_callback(f"MQTT подключён: {host}:{port}")
        except Exception as e:
            self.log_callback(f"MQTT ERROR: {e}")
            return None, None, None, None

        return client, host, port, user

    def apply_mqtt(self, host, port, user, pwd):
        self.mqtt, _, _, _ = self.create_mqtt_client(host, port, user, pwd)

    def send_mqtt(self, topic, payload, host, port, user, pwd):
        self.mqtt, host, port, user = self.create_mqtt_client(host, port, user, pwd)
        if not self.mqtt:
            return False

        confirmed = threading.Event()

        def on_temp_message(client, userdata, msg):
            try:
                if msg.payload.decode() == payload:
                    confirmed.set()
            except Exception:
                pass

        self.mqtt.message_callback_add(topic, on_temp_message)
        self.mqtt.subscribe(topic)

        try:
            self.mqtt.publish(topic, payload, retain=True)
        except Exception as e:
            self.log_callback(f"MQTT send ERROR: {e}")
            self.mqtt.message_callback_remove(topic)
            return False

        self.log_callback("Ожидаем подтверждение публикации...")
        if not confirmed.wait(timeout=3):
            self.log_callback("Нет подтверждения в топике, проверьте брокер или топик!")
            self.mqtt.message_callback_remove(topic)
            return False

        self.log_callback("Данные успешно опубликованы")
        self.mqtt.message_callback_remove(topic)
        return True
