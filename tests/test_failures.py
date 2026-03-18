import pytest

from chirp_sensor.driver import Chirp


def test_oserror_on_read(mock_bus):
    mock_bus.read_word_data.side_effect = OSError("I2C failure")
    sensor = Chirp(bus=1, address=0x20)

    with pytest.raises(OSError):
        sensor.read_moisture()


def test_invalid_address_set(mock_bus):
    sensor = Chirp(bus=1, address=0x20)

    with pytest.raises(ValueError):
        sensor.sensor_address = 200  # out of valid range
