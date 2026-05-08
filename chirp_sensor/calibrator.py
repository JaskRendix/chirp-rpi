from __future__ import annotations

import time
from dataclasses import dataclass
from statistics import mean

from chirp_sensor.driver import Chirp


@dataclass
class CalibrationResult:
    dry: int
    wet: int


class AutoCalibrator:
    """
    Auto-calibration helper with stability detection.
    """

    def __init__(
        self,
        sensor: Chirp,
        min_samples: int = 10,
        max_samples: int = 50,
        interval: float = 0.5,
        stability_threshold: float = 0.02,  # 2% variation
    ):
        self.sensor = sensor
        self.min_samples = min_samples
        self.max_samples = max_samples
        self.interval = interval
        self.stability_threshold = stability_threshold

    def _collect(self, label: str) -> int:
        values: list[int] = []
        print(f"Collecting samples for {label}…")

        for i in range(self.max_samples):
            raw = self.sensor.read_moisture()
            values.append(raw)
            print(f"  {label} sample {i+1}: {raw}")

            if i + 1 >= self.min_samples:
                window = values[-self.min_samples :]
                avg = mean(window)
                variation = (max(window) - min(window)) / avg if avg else 1.0

                if variation < self.stability_threshold:
                    print(f"  {label} stabilized after {i+1} samples.")
                    break

            time.sleep(self.interval)

        return int(mean(values[-self.min_samples :]))

    def run(self) -> CalibrationResult:
        print("=== Auto‑calibration ===")
        print("Step 1: Leave the sensor in dry air.")
        input("Press Enter when ready… ")

        dry = self._collect("dry")

        print("\nStep 2: Submerge the sensor in water.")
        input("Press Enter when ready… ")

        wet = self._collect("wet")

        print("\nCalibration complete.")
        print(f"Dry = {dry}, Wet = {wet}")

        return CalibrationResult(dry=dry, wet=wet)

    def write_to_toml(self, path: str, result: CalibrationResult) -> None:
        """
        Append or update dry/wet values in chirp.toml.
        """
        lines = []
        try:
            with open(path, "r") as f:
                lines = f.readlines()
        except FileNotFoundError:
            pass

        new_lines = []
        replaced_dry = replaced_wet = False

        for line in lines:
            if line.strip().startswith("dry"):
                new_lines.append(f"dry = {result.dry}\n")
                replaced_dry = True
            elif line.strip().startswith("wet"):
                new_lines.append(f"wet = {result.wet}\n")
                replaced_wet = True
            else:
                new_lines.append(line)

        if not replaced_dry:
            new_lines.append(f"dry = {result.dry}\n")
        if not replaced_wet:
            new_lines.append(f"wet = {result.wet}\n")

        with open(path, "w") as f:
            f.writelines(new_lines)

        print(f"Updated {path} with new calibration values.")
