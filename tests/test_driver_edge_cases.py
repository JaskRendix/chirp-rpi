import pytest

from chirp_sensor.driver import Chirp


@pytest.fixture(autouse=True)
def no_sleep(mocker):
    mocker.patch("time.sleep", return_value=None)


def test_busy_wait(mock_bus, mocker):
    def busy_sequence():
        # moisture busy loop
        yield from [1, 1, 1, 0]
        # temperature busy loop
        yield from [1, 1, 0]
        # light busy loop
        yield from [1, 1, 0]
        while True:
            yield 0

    mock_bus.read_byte_data.side_effect = busy_sequence()

    mock_bus.read_word_data.side_effect = [
        0x1000,
        0x2000,  # moisture
        0x1111,
        0x2222,  # temperature
        0x3333,  # light
    ]

    sensor = Chirp(bus=1, address=0x20)
    r = sensor.read()

    assert r.moisture == ((0x2000 >> 8) | ((0x2000 & 0xFF) << 8))
    assert r.temperature_c == round(0x2222 / 10.0, 1)
    assert r.light == 0x3333
