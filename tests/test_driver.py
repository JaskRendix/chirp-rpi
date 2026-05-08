from datetime import datetime

import pytest

from chirp_sensor.driver import Chirp, MoistureCalibration


@pytest.fixture
def mock_bus(mocker):
    bus = mocker.MagicMock()
    mocker.patch("chirp_sensor.driver.SMBus", return_value=bus)
    return bus


@pytest.fixture(autouse=True)
def no_sleep(mocker):
    mocker.patch("time.sleep", return_value=None)


def test_set_address_valid(mock_bus):
    sensor = Chirp(bus=1, address=0x20)
    sensor.sensor_address = 0x30
    assert sensor.address == 0x30
    mock_bus.write_byte_data.assert_called()


def test_set_address_invalid(mock_bus):
    sensor = Chirp(bus=1, address=0x20)
    with pytest.raises(ValueError):
        sensor.sensor_address = 200


def test_basic_read(mock_bus):
    mock_bus.read_word_data.side_effect = [
        0x1234,
        0x5678,  # moisture
        0x1111,
        0x2222,  # temperature
        0x3333,  # light
    ]
    mock_bus.read_byte_data.return_value = 0

    sensor = Chirp(bus=1, address=0x20)
    r = sensor.read()

    assert r.moisture == ((0x5678 >> 8) | ((0x5678 & 0xFF) << 8))
    assert r.temperature_c == round(((0x2222 >> 8) | ((0x2222 & 0xFF) << 8)) / 10.0, 1)
    assert r.light == 0x3333
    assert isinstance(r.timestamp, datetime)


def test_repeated_reads(mock_bus):
    mock_bus.read_word_data.side_effect = [
        0x1000,
        0x2000,
        0x3000,
        0x4000,
        0x5000,
        0x1000,
        0x2000,
        0x3000,
        0x4000,
        0x5000,
    ]
    mock_bus.read_byte_data.return_value = 0

    sensor = Chirp(bus=1, address=0x20)
    r1 = sensor.read()
    r2 = sensor.read()

    assert r1.moisture == r2.moisture
    assert r1.temperature_c == r2.temperature_c
    assert r1.light == r2.light


def test_busy_wait(mock_bus):
    def busy_seq():
        yield from [1, 1, 1, 0]  # moisture
        yield from [1, 1, 0]  # temp
        yield from [1, 1, 0]  # light
        while True:
            yield 0

    mock_bus.read_byte_data.side_effect = busy_seq()
    mock_bus.read_word_data.side_effect = [
        0x1000,
        0x2000,
        0x1111,
        0x2222,
        0x3333,
    ]

    sensor = Chirp(bus=1, address=0x20)
    r = sensor.read()

    assert r.moisture > 0
    assert r.temperature_c > 0
    assert r.light == 0x3333


def swap16(x):
    return (x >> 8) | ((x & 0xFF) << 8)


@pytest.mark.parametrize("raw", [0, 123, 250, 999])
def test_temperature_conversion(mock_bus, raw):
    mock_bus.read_word_data.side_effect = [raw, raw]
    mock_bus.read_byte_data.return_value = 0

    sensor = Chirp(bus=1, address=0x20)
    assert sensor.read_temperature_c() == round(swap16(raw) / 10.0, 1)


@pytest.mark.parametrize("raw", [0, 1, 1234, 65535])
def test_light_values(mock_bus, raw):
    mock_bus.read_word_data.return_value = raw
    mock_bus.read_byte_data.return_value = 0

    sensor = Chirp(bus=1, address=0x20)
    assert sensor.read_light() == swap16(raw)


def test_read_with_calibration(mock_bus):
    # moisture old/new, temp old/new, light
    mock_bus.read_word_data.side_effect = [
        0x1000,
        0x2000,
        0x3000,
        0x4000,
        0x5000,
    ]
    mock_bus.read_byte_data.return_value = 0

    cal = MoistureCalibration(dry=0x2000, wet=0x4000)

    sensor = Chirp(bus=1, address=0x20, calibration=cal)
    r = sensor.read()

    assert r.moisture_percent is not None
    assert 0.0 <= r.moisture_percent <= 100.0


def test_timestamp_monotonicity(mock_bus):
    mock_bus.read_word_data.side_effect = [
        0x1000,
        0x2000,
        0x3000,
        0x4000,
        0x5000,
        0x1000,
        0x2000,
        0x3000,
        0x4000,
        0x5000,
    ]
    mock_bus.read_byte_data.return_value = 0

    sensor = Chirp(bus=1, address=0x20)
    r1 = sensor.read()
    r2 = sensor.read()

    assert r2.timestamp >= r1.timestamp


def test_register_sequence(mock_bus):
    # moisture old/new, temp old/new, light
    mock_bus.read_word_data.side_effect = [
        0xAAAA,
        0xBBBB,
        0xCCCC,
        0xDDDD,
        0xEEEE,
    ]
    mock_bus.read_byte_data.return_value = 0

    sensor = Chirp(bus=1, address=0x20)
    sensor.read()

    # Expected register order:
    # 1. GET_CAP old
    # 2. GET_CAP new
    # 3. GET_TEMP old
    # 4. GET_TEMP new
    # 5. MEASURE_LIGHT (write)
    # 6. GET_LIGHT
    calls = [call[0][1] for call in mock_bus.read_word_data.call_args_list]
    assert calls == [
        sensor._GET_CAPACITANCE,
        sensor._GET_CAPACITANCE,
        sensor._GET_TEMPERATURE,
        sensor._GET_TEMPERATURE,
        sensor._GET_LIGHT,
    ]


def test_sleep_and_wake(mock_bus):
    sensor = Chirp(bus=1, address=0x20)

    sensor.sleep()
    mock_bus.write_byte.assert_called_with(0x20, sensor._SLEEP)

    # wake_up should swallow OSError and call sleep()
    mock_bus.read_byte_data.side_effect = OSError("fail")
    sensor.wake_up(wake_time=0.1)  # patched sleep prevents delay


def test_address_double_write(mock_bus):
    sensor = Chirp(bus=1, address=0x20)
    sensor.sensor_address = 0x30

    # Two writes required by firmware
    writes = [
        call for call in mock_bus.write_byte_data.call_args_list if call[0][2] == 0x30
    ]
    assert len(writes) == 2
