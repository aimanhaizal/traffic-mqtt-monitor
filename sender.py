"""Replay rows from a CSV file as JSON messages over MQTT."""

import json
import os

from dotenv import load_dotenv

load_dotenv()
import time
from pathlib import Path

import pandas as pd
import paho.mqtt.client as mqtt

CSV_PATH = Path(os.getenv("CSV_PATH", "TrafficVolumeData.csv"))
MQTT_HOST = os.getenv("MQTT_HOST", "127.0.0.1")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "traffic/data")
PUBLISH_INTERVAL = max(0.0, float(os.getenv("PUBLISH_INTERVAL", "1")))
REPLAY_LOOP = os.getenv("REPLAY_LOOP", "false").strip().lower() in {
    "1", "true", "yes", "y"
}


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"Connected to MQTT broker at {MQTT_HOST}:{MQTT_PORT}")
    else:
        print(f"MQTT connection failed: {reason_code}")


def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {CSV_PATH}. Set CSV_PATH or place the CSV in the project root."
        )

    data = pd.read_csv(CSV_PATH)
    if data.empty:
        raise ValueError("Dataset contains no rows.")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="traffic-csv-sender")
    client.on_connect = on_connect
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    client.loop_start()

    try:
        while True:
            for _, row in data.iterrows():
                # Convert pandas NaN/NA values to JSON null and numpy values to Python values.
                payload = {}
                for key, value in row.items():
                    if pd.isna(value):
                        payload[key] = None
                    else:
                        payload[key] = value.item() if hasattr(value, "item") else value
                message = json.dumps(payload, default=str, allow_nan=False)
                info = client.publish(MQTT_TOPIC, message, qos=0)
                info.wait_for_publish()
                print(f"Published {payload.get('date_time')} to {MQTT_TOPIC}")
                if PUBLISH_INTERVAL:
                    time.sleep(PUBLISH_INTERVAL)

            if not REPLAY_LOOP:
                break
    except KeyboardInterrupt:
        print("Stopping sender...")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
