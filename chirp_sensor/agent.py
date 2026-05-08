from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Deque

from chirp_sensor.driver import Chirp, ChirpReading


@dataclass
class MoistureSample:
    timestamp: datetime
    moisture_percent: float


class SoilAgent:
    def __init__(self, sensor: Chirp, history_size: int = 100):
        self.sensor = sensor
        self.history: Deque[MoistureSample] = deque(maxlen=history_size)

    def sample(self) -> ChirpReading:
        r = self.sensor.read()
        if r.moisture_percent is not None:
            self.history.append(
                MoistureSample(
                    timestamp=r.timestamp,
                    moisture_percent=r.moisture_percent,
                )
            )
        return r

    def estimate_drying_rate(self) -> float | None:
        if len(self.history) < 2:
            return None
        first = self.history[0]
        last = self.history[-1]
        dt_hours = (last.timestamp - first.timestamp).total_seconds() / 3600.0
        if dt_hours <= 0:
            return None
        return (first.moisture_percent - last.moisture_percent) / dt_hours

    def predict_hours_until(self, target_percent: float) -> float | None:
        if not self.history:
            return None
        rate = self.estimate_drying_rate()
        if rate is None or rate <= 0:
            return None
        current = self.history[-1].moisture_percent
        if current <= target_percent:
            return 0.0
        return (current - target_percent) / rate
