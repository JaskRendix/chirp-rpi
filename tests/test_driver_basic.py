from datetime import datetime

from chirp_sensor.driver import Chirp


def test_basic_read(mock_bus):
    # Fake register values
    mock_bus.read_word_data.side_effect = [
        0x1234,  # moisture old
        0x5678,  # moisture new
        0x1111,  # temp old
        0x2222,  # temp new
        0x3333,  # light
    ]
    mock_bus.read_byte_data.return_value = 0  # not busy

    sensor = Chirp(bus=1, address=0x20)
    r = sensor.read()

    assert r.moisture == 0x7856  # swapped bytes
    assert r.temperature_c == round((0x2222 / 10.0), 1)
    assert r.light == 0x3333
    assert isinstance(r.timestamp, datetime)
