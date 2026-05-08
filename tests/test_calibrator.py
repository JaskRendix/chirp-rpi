from unittest.mock import MagicMock

from chirp_sensor.calibrator import AutoCalibrator, CalibrationResult


def test_auto_calibrator_stability_detection():
    sensor = MagicMock()
    # Simulate stable readings
    sensor.read_moisture.side_effect = [100] * 50

    cal = AutoCalibrator(sensor, min_samples=5, max_samples=20, interval=0)
    result = cal._collect("dry")

    assert result == 100
    assert sensor.read_moisture.call_count <= 10  # should stop early


def test_auto_calibrator_run():
    sensor = MagicMock()

    # dry → 200, wet → 800
    sensor.read_moisture.side_effect = [200] * 5 + [  # dry samples
        800
    ] * 5  # wet samples

    cal = AutoCalibrator(sensor, min_samples=5, max_samples=20, interval=0)

    import builtins

    builtins.input = lambda _: ""

    result = cal.run()

    assert result.dry == 200
    assert result.wet == 800


def test_write_to_toml(tmp_path):
    path = tmp_path / "chirp.toml"
    path.write_text("bus = 1\naddress = 0x20\n")

    cal = AutoCalibrator(MagicMock())
    result = CalibrationResult(dry=123, wet=456)

    cal.write_to_toml(str(path), result)

    text = path.read_text()
    assert "dry = 123" in text
    assert "wet = 456" in text
