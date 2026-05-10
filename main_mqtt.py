#!/usr/bin/env python3
from __future__ import annotations

import json
import socket
import time

import paho.mqtt.client as mqtt

from chirp_sensor.config import Config, load_config
from chirp_sensor.driver import Chirp, MoistureCalibration


def publish_state(client: mqtt.Client, sensor: Chirp) -> None:
    cfg: Config = load_config()
    base_topic = cfg.mqtt_base

    r = sensor.read()
    payload = {
        "moisture_raw": r.moisture,
        "moisture_percent": r.moisture_percent,
        "temperature_c": r.temperature_c,
        "light": r.light,
        "timestamp": r.timestamp.isoformat(),
    }
    client.publish(f"{base_topic}/state", json.dumps(payload), retain=True)


def main() -> None:
    cfg: Config = load_config()

    calibration = (
        MoistureCalibration(cfg.dry, cfg.wet)
        if cfg.dry is not None and cfg.wet is not None
        else None
    )

    sensor = Chirp(
        bus=cfg.bus,
        address=cfg.address,
        calibration=calibration,
        busy_sleep=cfg.busy_sleep,
        read_timeout_s=cfg.read_timeout_s,
    )

    client_id = f"chirp-{socket.gethostname()}"
    client = mqtt.Client(client_id=client_id)

    client.connect(cfg.mqtt_host, cfg.mqtt_port, 60)
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


if __name__ == "__main__":
    main()
