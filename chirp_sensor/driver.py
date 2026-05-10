from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any, TypeVar

from smbus2 import SMBus

T = TypeVar("T")


class ChirpTimeoutError(TimeoutError):
    """Raised when the sensor does not become ready within the timeout."""


@dataclass
class MoistureCalibration:
    dry: int
    wet: int

    def to_percent(self, value: int) -> float:
        if self.wet == self.dry:
            return 0.0
        pct = (value - self.dry) * 100.0 / (self.wet - self.dry)
        return max(0.0, min(100.0, round(pct, 1)))


@dataclass
class ChirpReading:
    moisture: int
    moisture_percent: float | None
    temperature_c: float
    light: int
    timestamp: datetime


class Chirp:
    _GET_CAPACITANCE = 0x00
    _SET_ADDRESS = 0x01
    _GET_ADDRESS = 0x02
    _MEASURE_LIGHT = 0x03
    _GET_LIGHT = 0x04
    _GET_TEMPERATURE = 0x05
    _RESET = 0x06
    _GET_VERSION = 0x07
    _SLEEP = 0x08
    _GET_BUSY = 0x09

    def __init__(
        self,
        bus: int = 1,
        address: int = 0x20,
        calibration: MoistureCalibration | None = None,
        busy_sleep: float = 0.01,
        read_timeout_s: float = 1.0,
    ) -> None:
        self.bus_num = bus
        self.bus = SMBus(bus)
        self.address = address
        self.calibration = calibration
        self.busy_sleep = busy_sleep
        self.read_timeout_s = read_timeout_s

    def __enter__(self) -> "Chirp":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.bus.close()

    def _busy(self) -> bool:
        return self._retry(self.bus.read_byte_data, self.address, self._GET_BUSY) == 1

    def _read_reg16(self, reg: int) -> int:
        val = self._retry(self.bus.read_word_data, self.address, reg)
        return (val >> 8) | ((val & 0xFF) << 8)

    def _wait_ready(self) -> None:
        """Wait until the sensor clears the busy flag or raise ChirpTimeoutError."""
        deadline = time.monotonic() + self.read_timeout_s

        while self._busy():
            if time.monotonic() > deadline:
                raise ChirpTimeoutError(
                    f"Sensor at 0x{self.address:02X} did not become ready "
                    f"within {self.read_timeout_s:.2f}s"
                )
            time.sleep(self.busy_sleep)

    def _retry(
        self,
        func: Callable[..., T],
        *args: Any,
        retries: int = 3,
        **kwargs: Any,
    ) -> T:
        """Retry an I2C operation a few times before failing."""
        last_exc: Exception | None = None

        for _ in range(retries):
            try:
                return func(*args, **kwargs)
            except OSError as exc:
                last_exc = exc
                time.sleep(self.busy_sleep)

        assert last_exc is not None
        raise last_exc

    def reset(self) -> None:
        self._retry(self.bus.write_byte, self.address, self._RESET)

    def sleep(self) -> None:
        self._retry(self.bus.write_byte, self.address, self._SLEEP)

    def wake_up(self, wake_time: float = 1.0) -> None:
        try:
            self.bus.read_byte_data(self.address, self._GET_VERSION)
        except OSError:
            pass
        time.sleep(wake_time)

    @property
    def version(self) -> int:
        return self._retry(self.bus.read_byte_data, self.address, self._GET_VERSION)

    @property
    def sensor_address(self) -> int:
        return self._retry(self.bus.read_byte_data, self.address, self._GET_ADDRESS)

    @sensor_address.setter
    def sensor_address(self, new_addr: int) -> None:
        if not (3 <= new_addr <= 119):
            raise ValueError("I2C address must be between 3 and 119")
        self._retry(self.bus.write_byte_data, self.address, self._SET_ADDRESS, new_addr)
        self._retry(self.bus.write_byte_data, self.address, self._SET_ADDRESS, new_addr)
        self.reset()
        self.address = new_addr

    def read_moisture(self) -> int:
        _ = self._read_reg16(self._GET_CAPACITANCE)
        self._wait_ready()
        return self._read_reg16(self._GET_CAPACITANCE)

    def read_temperature_c(self) -> float:
        _ = self._read_reg16(self._GET_TEMPERATURE)
        self._wait_ready()
        raw = self._read_reg16(self._GET_TEMPERATURE)
        return round(raw / 10.0, 1)

    def read_light(self) -> int:
        self._retry(self.bus.write_byte, self.address, self._MEASURE_LIGHT)
        self._wait_ready()
        return self._read_reg16(self._GET_LIGHT)

    def read(self) -> ChirpReading:
        ts = datetime.now()
        moist = self.read_moisture()
        temp_c = self.read_temperature_c()
        light = self.read_light()
        pct = self.calibration.to_percent(moist) if self.calibration else None
        return ChirpReading(
            moisture=moist,
            moisture_percent=pct,
            temperature_c=temp_c,
            light=light,
            timestamp=ts,
        )
