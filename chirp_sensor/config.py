from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import tomllib

# Default search locations
CONFIG_PATHS = [
    Path("chirp.toml"),  # project root / working directory
    Path("/etc/chirp.toml"),  # system-wide config
]


@dataclass
class Config:
    bus: int = 1
    address: int = 0x20
    dry: int | None = None
    wet: int | None = None

    busy_sleep: float = 0.01
    read_timeout_s: float = 1.0

    smoothing_alpha: float = 1.0
    watering_threshold: float = 3.0
    min_hours_for_rate: float = 1.0
    persist_path: str | None = None

    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    mqtt_base: str = "home/chirp/sensor"

    prom_port: int = 9100
    rest_port: int = 8000


def load_config() -> Config:
    """
    Load chirp.toml from known locations.
    Missing fields fall back to defaults.
    """
    data = {}

    for path in CONFIG_PATHS:
        if path.exists():
            with path.open("rb") as f:
                data = tomllib.load(f)
            break

    cfg = Config()

    # Sensor settings
    cfg.bus = data.get("bus", cfg.bus)
    cfg.address = data.get("address", cfg.address)
    cfg.dry = data.get("dry", cfg.dry)
    cfg.wet = data.get("wet", cfg.wet)
    cfg.busy_sleep = data.get("busy_sleep", cfg.busy_sleep)
    cfg.read_timeout_s = data.get("read_timeout_s", cfg.read_timeout_s)
    cfg.smoothing_alpha = data.get("smoothing_alpha", cfg.smoothing_alpha)
    cfg.watering_threshold = data.get("watering_threshold", cfg.watering_threshold)
    cfg.min_hours_for_rate = data.get("min_hours_for_rate", cfg.min_hours_for_rate)
    cfg.persist_path = data.get("persist_path", cfg.persist_path)

    # MQTT
    cfg.mqtt_host = data.get("mqtt_host", cfg.mqtt_host)
    cfg.mqtt_port = data.get("mqtt_port", cfg.mqtt_port)
    cfg.mqtt_base = data.get("mqtt_base", cfg.mqtt_base)

    # Prometheus
    cfg.prom_port = data.get("prom_port", cfg.prom_port)

    # REST API
    cfg.rest_port = data.get("rest_port", cfg.rest_port)

    return cfg
