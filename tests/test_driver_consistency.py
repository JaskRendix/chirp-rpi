from chirp_sensor.driver import Chirp


def test_repeated_reads(mock_bus):
    mock_bus.read_word_data.side_effect = [
        0x1000,
        0x2000,  # moisture
        0x3000,
        0x4000,  # temp
        0x5000,  # light
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
