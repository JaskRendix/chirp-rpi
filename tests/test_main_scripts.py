import importlib

import pytest


@pytest.mark.parametrize(
    "module",
    [
        "main_rest",
        "main_prom",
        "main_agent",
        "main_mqtt",
    ],
)
def test_main_scripts_import(module):
    imported = importlib.import_module(module)
    assert imported is not None
