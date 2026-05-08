import pytest

from chirp_sensor.driver import MoistureCalibration


def test_calibration_percent_basic():
    cal = MoistureCalibration(dry=200, wet=800)
    assert cal.to_percent(200) == 0.0
    assert cal.to_percent(800) == 100.0
    assert cal.to_percent(500) == 50.0


@pytest.mark.parametrize(
    "value,expected", [(200, 0.0), (800, 100.0), (500, 50.0), (1000, 100.0), (0, 0.0)]
)
def test_calibration_parametrized(value, expected):
    cal = MoistureCalibration(dry=200, wet=800)
    assert cal.to_percent(value) == expected


def test_invalid_calibration_range():
    cal = MoistureCalibration(dry=500, wet=500)
    assert cal.to_percent(500) == 0.0  # safe fallback
