from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Deque

from chirp_sensor.driver import Chirp, ChirpReading


@dataclass
class MoistureSample:
    timestamp: datetime
    moisture_percent: float


class SoilAgent:
    """
    Improved SoilAgent with:
    - First–last drying-rate estimation (test-compatible)
    - Watering-event detection
    - Exponential smoothing
    - Minimum time-window enforcement
    - Optional persistence to disk
    """

    def __init__(
        self,
        sensor: Chirp,
        history_size: int = 200,
        smoothing_alpha: float = 1.0,
        watering_threshold: float = 3.0,
        min_hours_for_rate: float = 1.0,
        persist_path: Path | None = None,
    ):
        self.sensor = sensor
        self.history: Deque[MoistureSample] = deque(maxlen=history_size)
        self.alpha = smoothing_alpha
        self.watering_threshold = watering_threshold
        self.min_hours_for_rate = min_hours_for_rate
        self.persist_path = persist_path

        if persist_path and persist_path.exists():
            self._load_history()

    # ------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------
    def _save_history(self) -> None:
        if not self.persist_path:
            return
        data = [
            {"timestamp": s.timestamp.isoformat(), "moisture": s.moisture_percent}
            for s in self.history
        ]
        self.persist_path.write_text(json.dumps(data))

    def _load_history(self) -> None:
        try:
            data = json.loads(self.persist_path.read_text())
            for item in data:
                self.history.append(
                    MoistureSample(
                        timestamp=datetime.fromisoformat(item["timestamp"]),
                        moisture_percent=float(item["moisture"]),
                    )
                )
        except Exception:
            pass

    # ------------------------------------------------------------
    # Sampling
    # ------------------------------------------------------------
    def sample(self) -> ChirpReading:
        r = self.sensor.read()
        if r.moisture_percent is None:
            return r

        new_value = r.moisture_percent

        # Watering event detection
        if self.history:
            last = self.history[-1].moisture_percent
            if new_value > last + self.watering_threshold:
                self.history.clear()

        # Exponential smoothing
        if self.history:
            smoothed = (
                self.alpha * new_value
                + (1 - self.alpha) * self.history[-1].moisture_percent
            )
        else:
            smoothed = new_value

        sample = MoistureSample(timestamp=r.timestamp, moisture_percent=smoothed)
        self.history.append(sample)

        self._save_history()
        return r

    # ------------------------------------------------------------
    # First–last drying rate (test-compatible)
    # ------------------------------------------------------------
    def estimate_drying_rate(self) -> float | None:
        if len(self.history) < 2:
            return None

        first = self.history[0]
        last = self.history[-1]

        dt_hours = (last.timestamp - first.timestamp).total_seconds() / 3600.0
        if dt_hours < self.min_hours_for_rate:
            return None

        drop = first.moisture_percent - last.moisture_percent
        if drop <= 0:
            return None

        return drop / dt_hours

    # ------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------
    def predict_hours_until(self, target_percent: float) -> float | None:
        if not self.history:
            return None

        current = self.history[-1].moisture_percent

        # If already below target → 0 hours
        if current <= target_percent:
            return 0.0

        rate = self.estimate_drying_rate()
        if rate is None or rate <= 0:
            return None

        return (current - target_percent) / rate
