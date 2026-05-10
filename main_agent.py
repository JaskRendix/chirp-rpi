#!/usr/bin/env python3
from __future__ import annotations

import time
from pathlib import Path

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
        busy_sleep=cfg.busy_sleep,
        read_timeout_s=cfg.read_timeout_s,
    )

    agent = SoilAgent(
        sensor,
        smoothing_alpha=cfg.smoothing_alpha,
        watering_threshold=cfg.watering_threshold,
        min_hours_for_rate=cfg.min_hours_for_rate,
        persist_path=Path(cfg.persist_path) if cfg.persist_path else None,
    )

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
