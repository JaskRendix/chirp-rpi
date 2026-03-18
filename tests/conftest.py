import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def mock_bus(mocker):
    bus = MagicMock()
    mocker.patch("chirp_sensor.driver.SMBus", return_value=bus)
    return bus
