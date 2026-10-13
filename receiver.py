"""Subscribe to traffic MQTT messages, predict volume, and serve a Flask dashboard."""

import json
import os

from dotenv import load_dotenv

load_dotenv()
from collections import deque
from pathlib import Path
from threading import Lock

import joblib
import pandas as pd
import paho.mqtt.client as mqtt
from flask import Flask, render_template

from features import make_features

MQTT_HOST = os.getenv("MQTT_HOST", "127.0.0.1")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "traffic/data")
FLASK_HOST = os.getenv("FLASK_HOST", "127.0.0.1")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5018"))
MODEL_PATH = Path(os.getenv("MODEL_PATH", "traffic_model.pkl"))
MAX_MESSAGES = max(1, int(os.getenv("MAX_MESSAGES", "10")))

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Model not found: {MODEL_PATH}. Run `python ml_model.py` first."
    )

model = joblib.load(MODEL_PATH)
print(f"Traffic prediction model loaded from {MODEL_PATH}")

app = Flask(__name__)
messages = deque(maxlen=MAX_MESSAGES)
messages_lock = Lock()


def predict_traffic(data):
    features = make_features(pd.DataFrame([data]))
    return round(float(model.predict(features)[0]))


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"Connected to MQTT broker at {MQTT_HOST}:{MQTT_PORT}")
        client.subscribe(MQTT_TOPIC)
        print(f"Subscribed to topic: {MQTT_TOPIC}")
    else:
        print(f"MQTT connection failed: {reason_code}")


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("MQTT payload must be a JSON object.")

        prediction = predict_traffic(data)
        data["predicted_traffic"] = prediction
        with messages_lock:
            messages.appendleft(data)
        print(
            f"Received timestamp={data.get('date_time')} "
            f"actual={data.get('traffic_volume')} predicted={prediction}"
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError) as exc:
        print(f"Skipping invalid MQTT message: {exc}")
    except Exception as exc:
        print(f"Could not process MQTT message: {exc}")


@app.route("/")
def index():
    with messages_lock:
        recent_messages = list(messages)
    return render_template("index.html", messages=recent_messages)


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="traffic-dashboard-receiver")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    client.loop_start()
    try:
        app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False, use_reloader=False)
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
