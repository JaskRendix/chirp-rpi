import pytest

from chirp_sensor.driver import Chirp, MoistureCalibration


@pytest.mark.parametrize(
    "value,expected",
    [
        (200, 0.0),
        (800, 100.0),
        (500, 50.0),
        (1000, 100.0),
        (0, 0.0),
    ],
)
def test_moisture_percent_param(value, expected):
    cal = MoistureCalibration(dry=200, wet=800)
    assert cal.to_percent(value) == expected


def swap16(x):
    return (x >> 8) | ((x & 0xFF) << 8)


@pytest.mark.parametrize("raw", [0, 123, 250, 999])
def test_temperature_conversion(mock_bus, raw):
    mock_bus.read_word_data.side_effect = [raw, raw]
    mock_bus.read_byte_data.return_value = 0

    sensor = Chirp(bus=1, address=0x20)
    expected = round(swap16(raw) / 10.0, 1)
    assert sensor.read_temperature_c() == expected


@pytest.mark.parametrize("raw", [0, 1, 1234, 65535])
def test_light_values(mock_bus, raw):
    mock_bus.read_word_data.return_value = raw
    mock_bus.read_byte_data.return_value = 0

    sensor = Chirp(bus=1, address=0x20)
    assert sensor.read_light() == swap16(raw)
