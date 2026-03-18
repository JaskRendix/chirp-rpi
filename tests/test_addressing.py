import pytest

from chirp_sensor.driver import Chirp


def test_set_address_valid(mock_bus):
    sensor = Chirp(bus=1, address=0x20)
    sensor.sensor_address = 0x30
    assert sensor.address == 0x30
    mock_bus.write_byte_data.assert_called()


def test_set_address_invalid(mock_bus):
    sensor = Chirp(bus=1, address=0x20)
    with pytest.raises(ValueError):
        sensor.sensor_address = 200  # out of range
