#!/usr/bin/env python3
from __future__ import annotations

import time

from chirp_sensor.agent import SoilAgent
from chirp_sensor.config import Config, load_config
from chirp_sensor.driver import Chirp, MoistureCalibration

if __name__ == "__main__":
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

    agent = SoilAgent(sensor)

    try:
        while True:
            r = agent.sample()
            rate = agent.estimate_drying_rate()
            eta = agent.predict_hours_until(30.0)

            print(
                f"[{r.timestamp.isoformat()}] "
                f"moist={r.moisture_percent}% temp={r.temperature_c}C light={r.light}"
            )
            if rate is not None:
                print(f"  drying_rate ≈ {rate:.2f}%/h")
            if eta is not None:
                print(f"  ETA to 30% ≈ {eta:.1f} h")
            print()

            time.sleep(300)
    except KeyboardInterrupt:
        pass
