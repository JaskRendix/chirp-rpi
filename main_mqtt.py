import json
import socket
import time

import paho.mqtt.client as mqtt

from chirp_sensor.driver import Chirp, MoistureCalibration

MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_BASE = "home/chirp/basil"  # adjust
CLIENT_ID = f"chirp-{socket.gethostname()}"


def publish_state(client: mqtt.Client, sensor: Chirp):
    r = sensor.read()
    payload = {
        "moisture_raw": r.moisture,
        "moisture_percent": r.moisture_percent,
        "temperature_c": r.temperature_c,
        "light": r.light,
        "timestamp": r.timestamp.isoformat(),
    }
    client.publish(f"{MQTT_BASE}/state", json.dumps(payload), retain=True)


if __name__ == "__main__":
    calibration = MoistureCalibration(dry=240, wet=750)
    sensor = Chirp(bus=1, address=0x20, calibration=calibration)

    client = mqtt.Client(client_id=CLIENT_ID)
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_start()

    try:
        while True:
            publish_state(client, sensor)
            time.sleep(30)
    except KeyboardInterrupt:
        pass
    finally:
        client.loop_stop()
        client.disconnect()
