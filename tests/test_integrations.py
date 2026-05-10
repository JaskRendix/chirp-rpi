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


def test_main_agent_creates_agents_for_each_address(mocker):
    mocker.patch(
        "main_agent.scan_for_chirp",
        return_value=[0x20, 0x21, 0x22],
    )

    fake_sensor = MagicMock()
    mock_chirp = mocker.patch(
        "main_agent.Chirp",
        return_value=fake_sensor,
    )

    fake_agent = MagicMock()
    mock_agent = mocker.patch(
        "main_agent.SoilAgent",
        return_value=fake_agent,
    )

    mod = importlib.import_module("main_agent")

    cfg = mod.load_config()
    calibration = None
    addresses = mod.scan_for_chirp(cfg.bus)

    agents = []
    for addr in addresses:
        sensor = mod.Chirp(
            bus=cfg.bus,
            address=addr,
            calibration=calibration,
            busy_sleep=cfg.busy_sleep,
            read_timeout_s=cfg.read_timeout_s,
        )
        agent = mod.SoilAgent(
            sensor,
            smoothing_alpha=cfg.smoothing_alpha,
            watering_threshold=cfg.watering_threshold,
            min_hours_for_rate=cfg.min_hours_for_rate,
            persist_path=None,
        )
        agents.append(agent)

    assert len(agents) == 3
    assert mock_chirp.call_count == 3
    assert mock_agent.call_count == 3

    called_addresses = [call.kwargs["address"] for call in mock_chirp.call_args_list]
    assert called_addresses == [0x20, 0x21, 0x22]


def test_main_agent_samples_all_agents(mocker):
    mocker.patch("main_agent.scan_for_chirp", return_value=[0x20, 0x21])

    fake_sensor = MagicMock()
    fake_sensor.read.return_value = MagicMock(
        moisture=100,
        moisture_percent=50.0,
        temperature_c=20.0,
        light=123,
        timestamp=datetime(2026, 1, 1),
    )
    mocker.patch("main_agent.Chirp", return_value=fake_sensor)

    fake_agent = MagicMock()
    fake_agent.sample.return_value = fake_sensor.read.return_value
    mocker.patch("main_agent.SoilAgent", return_value=fake_agent)

    mod = importlib.import_module("main_agent")

    cfg = mod.load_config()
    addresses = mod.scan_for_chirp(cfg.bus)

    agents = [mod.SoilAgent(fake_sensor) for _ in addresses]

    for agent in agents:
        r = agent.sample()
        assert r.moisture == 100

    assert fake_agent.sample.call_count == 2
