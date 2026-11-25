"""Shared MQTT helpers: every client connects over TLS (8883) with its own account."""
import os

import paho.mqtt.client as mqtt

BROKER = os.environ.get("BROKER", "mosquitto")
PORT = int(os.environ.get("BROKER_PORT", "8883"))
CA_FILE = os.environ.get("CA_FILE", "/certs/ca.crt")

TOPIC_TEMP = "factory/machine1/temperature"
TOPIC_CTRL = "factory/machine1/control"


def connect(client_id, user, password):
    """Connect over TLS, trusting only the lab CA. Returns a connected client (not looping yet)."""
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
    client.username_pw_set(user, password)
    client.tls_set(ca_certs=CA_FILE)
    client.connect(BROKER, PORT, keepalive=30)
    return client
