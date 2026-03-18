from chirp_sensor.driver import MoistureCalibration


def test_calibration_percent():
    cal = MoistureCalibration(dry=200, wet=800)
    assert cal.to_percent(200) == 0.0
    assert cal.to_percent(800) == 100.0
    assert cal.to_percent(500) == 50.0
    assert cal.to_percent(1000) == 100.0  # clamped
    assert cal.to_percent(0) == 0.0  # clamped
