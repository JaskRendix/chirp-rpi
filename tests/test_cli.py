from unittest.mock import MagicMock, patch

import pytest

from chirpctl import main as cli_main


class ArgparseRunner:
    """
    Minimal runner for argparse CLIs.
    It simulates: python chirpctl <args...>
    """

    def invoke(self, args):
        with patch("sys.argv", ["chirpctl"] + args):
            try:
                cli_main()
                return MagicMock(exit_code=0)
            except SystemExit as e:
                return MagicMock(exit_code=e.code)


@pytest.fixture
def runner():
    return ArgparseRunner()


@pytest.fixture(autouse=True)
def mock_smbus(mocker):
    fake_bus = MagicMock()
    fake_bus.read_word_data.return_value = 1234
    fake_bus.read_byte_data.return_value = 0
    mocker.patch("chirp_sensor.driver.SMBus", return_value=fake_bus)


class FakeReading:
    moisture = 100
    moisture_percent = 50.0
    temperature_c = 20.0
    light = 123
    timestamp = __import__("datetime").datetime(2026, 1, 1, 0, 0, 0)


def test_cli_read(runner, mocker):
    fake_sensor = MagicMock()
    fake_sensor.read.return_value = FakeReading()
    mocker.patch("chirpctl.Chirp", return_value=fake_sensor)

    result = runner.invoke(["read"])
    assert result.exit_code == 0


def test_cli_moisture(runner, mocker):
    fake_sensor = MagicMock()
    fake_sensor.read_moisture.return_value = 1234
    mocker.patch("chirpctl.Chirp", return_value=fake_sensor)

    result = runner.invoke(["moisture"])
    assert result.exit_code == 0


def test_cli_temp(runner, mocker):
    fake_sensor = MagicMock()
    fake_sensor.read_temperature_c.return_value = 22.5
    mocker.patch("chirpctl.Chirp", return_value=fake_sensor)

    result = runner.invoke(["temp"])
    assert result.exit_code == 0


def test_cli_light(runner, mocker):
    fake_sensor = MagicMock()
    fake_sensor.read_light.return_value = 999
    mocker.patch("chirpctl.Chirp", return_value=fake_sensor)

    result = runner.invoke(["light"])
    assert result.exit_code == 0


def test_cli_version(runner, mocker):
    fake_sensor = MagicMock()
    fake_sensor.version = 42
    mocker.patch("chirpctl.Chirp", return_value=fake_sensor)

    result = runner.invoke(["version"])
    assert result.exit_code == 0


def test_cli_calibrate_dry(runner, mocker):
    fake_sensor = MagicMock()
    fake_sensor.read_moisture.return_value = 111
    mocker.patch("chirpctl.Chirp", return_value=fake_sensor)

    result = runner.invoke(["calibrate", "dry"])
    assert result.exit_code == 0


def test_cli_calibrate_wet(runner, mocker):
    fake_sensor = MagicMock()
    fake_sensor.read_moisture.return_value = 222
    mocker.patch("chirpctl.Chirp", return_value=fake_sensor)

    result = runner.invoke(["calibrate", "wet"])
    assert result.exit_code == 0


def test_cli_sleep(runner, mocker):
    fake_sensor = MagicMock()
    mocker.patch("chirpctl.Chirp", return_value=fake_sensor)

    result = runner.invoke(["sleep"])
    assert result.exit_code == 0
    fake_sensor.sleep.assert_called_once()


def test_cli_wake(runner, mocker):
    fake_sensor = MagicMock()
    mocker.patch("chirpctl.Chirp", return_value=fake_sensor)

    result = runner.invoke(["wake"])
    assert result.exit_code == 0
    fake_sensor.wake_up.assert_called_once()


def test_cli_address_set(runner, mocker):
    fake_sensor = MagicMock()
    mocker.patch("chirpctl.Chirp", return_value=fake_sensor)

    result = runner.invoke(["address", "set", "33"])
    assert result.exit_code == 0
    assert fake_sensor.sensor_address == 33


def test_cli_debug(runner, mocker):
    fake_sensor = MagicMock()
    fake_sensor.read_moisture.return_value = 100
    fake_sensor.read_temperature_c.return_value = 20.0
    fake_sensor.read_light.return_value = 123
    fake_sensor.version = 1
    fake_sensor.address = 0x20
    fake_sensor._busy.return_value = False

    mocker.patch("chirpctl.Chirp", return_value=fake_sensor)

    result = runner.invoke(["debug"])
    assert result.exit_code == 0


def test_cli_rest(runner, mocker):
    mocker.patch("main_rest.create_app", return_value=MagicMock())
    mocker.patch("uvicorn.run")
    result = runner.invoke(["rest"])
    assert result.exit_code == 0


def test_cli_mqtt(runner, mocker):
    mocker.patch("main_mqtt.main")
    result = runner.invoke(["mqtt"])
    assert result.exit_code == 0


def test_cli_prom(runner, mocker):
    mocker.patch("main_prom.main")
    result = runner.invoke(["prom"])
    assert result.exit_code == 0
