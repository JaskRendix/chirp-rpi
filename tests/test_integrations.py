import importlib
from datetime import datetime
from unittest.mock import MagicMock

import pytest


@pytest.mark.parametrize(
    "module", ["main_rest", "main_prom", "main_agent", "main_mqtt"]
)
def test_main_scripts_import(module):
    assert importlib.import_module(module)


def test_main_rest_create_app(mocker):
    mocker.patch("chirp_sensor.driver.Chirp")
    mod = importlib.import_module("main_rest")
    app = mod.create_app()
    assert app is not None
    assert hasattr(app, "router")


def test_main_prom_create_exporter(mocker):
    mocker.patch("chirp_sensor.driver.Chirp")
    mod = importlib.import_module("main_prom")
    exporter = mod.create_exporter()
    assert callable(exporter)


class FakeReading:
    moisture = 100
    moisture_percent = 50.0
    temperature_c = 20.0
    light = 123
    timestamp = datetime(2026, 1, 1, 0, 0, 0)


def test_main_mqtt_publish_state(mocker):
    mocker.patch("chirp_sensor.driver.Chirp")
    mock_client = MagicMock()

    fake_sensor = MagicMock()
    fake_sensor.read.return_value = FakeReading()

    mod = importlib.import_module("main_mqtt")
    mod.publish_state(mock_client, fake_sensor)

    mock_client.publish.assert_called()


def test_main_agent_sample_once(mocker):
    mock_sensor = MagicMock()
    mock_sensor.read.return_value = MagicMock(
        moisture=100,
        moisture_percent=50.0,
        temperature_c=20.0,
        light=123,
        timestamp=None,
    )
    mocker.patch("chirp_sensor.driver.Chirp", return_value=mock_sensor)

    mod = importlib.import_module("main_agent")
    agent = mod.SoilAgent(mock_sensor)
    r = agent.sample()
    assert r.moisture == 100
