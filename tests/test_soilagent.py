import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from chirp_sensor.agent import SoilAgent
from chirp_sensor.driver import ChirpReading


class DummySensor:
    """A fake Chirp sensor returning controlled readings."""

    def __init__(self, values):
        self.values = values
        self.index = 0

    def read(self):
        v = self.values[self.index]
        self.index = min(self.index + 1, len(self.values) - 1)
        return v


def make_reading(moist, ts=None):
    return ChirpReading(
        moisture=0,
        moisture_percent=moist,
        temperature_c=20.0,
        light=100,
        timestamp=ts or datetime.now(),
    )


def test_sample_adds_smoothed_values():
    sensor = DummySensor(
        [
            make_reading(50.0),
            make_reading(40.0),
        ]
    )
    agent = SoilAgent(sensor, smoothing_alpha=0.5)

    r1 = agent.sample()
    assert len(agent.history) == 1
    assert agent.history[-1].moisture_percent == pytest.approx(50.0)

    r2 = agent.sample()
    # smoothed = 0.5*40 + 0.5*50 = 45
    assert agent.history[-1].moisture_percent == pytest.approx(45.0)


def test_watering_event_resets_history():
    sensor = DummySensor(
        [
            make_reading(40.0),
            make_reading(42.0),
            make_reading(60.0),  # jump > threshold
        ]
    )
    agent = SoilAgent(sensor, watering_threshold=3.0)

    agent.sample()
    agent.sample()
    assert len(agent.history) == 2

    agent.sample()
    # history should reset because 60 > 42 + 3
    assert len(agent.history) == 1
    assert agent.history[-1].moisture_percent == pytest.approx(60.0)


def test_drying_rate_linear_regression():
    now = datetime.now()
    samples = [
        make_reading(60.0, now),
        make_reading(55.0, now + timedelta(hours=1)),
        make_reading(50.0, now + timedelta(hours=2)),
    ]
    sensor = DummySensor(samples)
    agent = SoilAgent(sensor, min_hours_for_rate=0)

    agent.sample()
    agent.sample()
    agent.sample()

    rate = agent.estimate_drying_rate()
    # Moisture drops 10% over 2 hours → 5%/h
    assert rate == pytest.approx(5.0)


def test_drying_rate_requires_min_hours():
    now = datetime.now()
    samples = [
        make_reading(60.0, now),
        make_reading(59.0, now + timedelta(minutes=10)),
    ]
    sensor = DummySensor(samples)
    agent = SoilAgent(sensor, min_hours_for_rate=1.0)

    agent.sample()
    agent.sample()

    assert agent.estimate_drying_rate() is None


def test_predict_hours_until():
    now = datetime.now()
    samples = [
        make_reading(60.0, now),
        make_reading(50.0, now + timedelta(hours=2)),
    ]
    sensor = DummySensor(samples)
    agent = SoilAgent(sensor, min_hours_for_rate=0)

    agent.sample()
    agent.sample()

    eta = agent.predict_hours_until(40.0)
    # rate = 5%/h, drop from 50 → 40 = 10% → 2 hours
    assert eta == pytest.approx(2.0)


def test_predict_returns_zero_if_target_reached():
    now = datetime.now()
    samples = [
        make_reading(30.0, now),
    ]
    sensor = DummySensor(samples)
    agent = SoilAgent(sensor)

    agent.sample()
    assert agent.predict_hours_until(40.0) == 0.0


def test_predict_none_if_rate_invalid():
    now = datetime.now()
    samples = [
        make_reading(40.0, now),
        make_reading(42.0, now + timedelta(hours=1)),  # moisture rising
    ]
    sensor = DummySensor(samples)
    agent = SoilAgent(sensor, min_hours_for_rate=0)

    agent.sample()
    agent.sample()

    assert agent.predict_hours_until(30.0) is None


def test_persistence_load_and_save():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "history.json"

        # First agent: write history
        sensor1 = DummySensor([make_reading(50.0)])
        agent1 = SoilAgent(sensor1, persist_path=path)
        agent1.sample()
        assert path.exists()

        # Second agent: load history
        sensor2 = DummySensor([make_reading(40.0)])
        agent2 = SoilAgent(sensor2, persist_path=path)
        assert len(agent2.history) == 1
        assert agent2.history[-1].moisture_percent == pytest.approx(50.0)

        # Append new sample and ensure save works
        agent2.sample()
        data = json.loads(path.read_text())
        assert len(data) == 2
