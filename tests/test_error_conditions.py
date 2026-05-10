import importlib

import pytest

from chirp_sensor.driver import Chirp


@pytest.mark.parametrize(
    "module", ["main_rest", "main_prom", "main_agent", "main_mqtt"]
)
def test_main_scripts_import(module):
    assert importlib.import_module(module)


def test_invalid_register_value_none(mock_bus):
    mock_bus.read_word_data.return_value = None
    mock_bus.read_byte_data.return_value = 0

    sensor = Chirp(bus=1, address=0x20)
    with pytest.raises(TypeError):
        sensor.read_moisture()


def test_invalid_register_value_negative(mock_bus):
    mock_bus.read_word_data.side_effect = [-1, -1]
    mock_bus.read_byte_data.return_value = 0

    sensor = Chirp(bus=1, address=0x20)
    # Driver does NOT validate negative values, so this should NOT raise
    result = sensor.read_temperature_c()
    assert isinstance(result, float)


def test_invalid_busy_flag(mock_bus):
    # Busy flag invalid -> treated as NOT busy in this driver
    mock_bus.read_byte_data.return_value = 5
    mock_bus.read_word_data.return_value = 0x1000

    sensor = Chirp(bus=1, address=0x20)
    # Should NOT raise TimeoutError
    result = sensor.read_moisture()
    assert isinstance(result, int)


def test_temperature_read_failure(mock_bus):
    # old temp, then 3 failures (retry attempts)
    mock_bus.read_word_data.side_effect = [
        0x1000,
        OSError("temp fail"),
        OSError("temp fail"),
        OSError("temp fail"),
    ]
    mock_bus.read_byte_data.return_value = 0

    sensor = Chirp(bus=1, address=0x20)
    with pytest.raises(OSError):
        sensor.read_temperature_c()


def test_light_read_failure(mock_bus):
    # moisture old/new, temp old/new
    mock_bus.read_word_data.side_effect = [
        0x1000,
        0x2000,  # moisture
        0x3000,
        0x4000,  # temperature
        OSError("light failure"),
        OSError("light failure"),
        OSError("light failure"),
    ]
    mock_bus.read_byte_data.return_value = 0

    sensor = Chirp(bus=1, address=0x20)
    with pytest.raises(OSError):
        sensor.read()


def test_moisture_read_failure(mock_bus):
    mock_bus.read_word_data.side_effect = OSError("moisture failure")
    mock_bus.read_byte_data.return_value = 0

    sensor = Chirp(bus=1, address=0x20)
    with pytest.raises(OSError):
        sensor.read_moisture()


def test_wake_up_swallows_oserror(mock_bus, mocker):
    mock_bus.read_byte_data.side_effect = OSError("fail")
    sleep_spy = mocker.spy(__import__("time"), "sleep")

    sensor = Chirp(bus=1, address=0x20)
    sensor.wake_up(wake_time=0.1)

    # OSError should be swallowed
    sleep_spy.assert_called()


def test_read_timeout_simulation(mock_bus, mocker):
    # Simulate infinite busy loop
    mock_bus.read_byte_data.return_value = 1
    mock_bus.read_word_data.return_value = 0x1000

    # Add a manual timeout to break the loop
    mocker.patch(
        "time.sleep", side_effect=[None, None, None, pytest.raises(TimeoutError)]
    )

    sensor = Chirp(bus=1, address=0x20)

    with pytest.raises(Exception):
        sensor.read_moisture()
