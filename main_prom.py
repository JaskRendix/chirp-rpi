#!/usr/bin/env python3
from __future__ import annotations

import time
from collections.abc import Callable

from prometheus_client import Gauge, start_http_server

from chirp_sensor.config import Config, load_config
from chirp_sensor.driver import Chirp, MoistureCalibration


def create_exporter() -> Callable[[float], None]:
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
    )

    g_moist = Gauge("chirp_moisture_raw", "Raw moisture reading")
    g_moist_pct = Gauge("chirp_moisture_percent", "Moisture percent")
    g_temp = Gauge("chirp_temperature_celsius", "Temperature in Celsius")
    g_light = Gauge("chirp_light", "Light reading (0=bright, 65535=dark)")

    def update(interval: float = 10.0) -> None:
        while True:
            r = sensor.read()
            g_moist.set(r.moisture)
            if r.moisture_percent is not None:
                g_moist_pct.set(r.moisture_percent)
            g_temp.set(r.temperature_c)
            g_light.set(r.light)
            time.sleep(interval)

    return update


def main() -> None:
    cfg: Config = load_config()

    exporter = create_exporter()

    start_http_server(cfg.prom_port)
    exporter(10.0)


if __name__ == "__main__":
    main()
