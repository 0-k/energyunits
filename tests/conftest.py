"""Shared pytest fixtures."""

import pytest

from energyunits.exchange_rate import exchange_rate_registry
from energyunits.inflation import inflation_registry
from energyunits.registry import registry
from energyunits.substance import substance_registry


@pytest.fixture(autouse=True)
def _isolated_registries():
    """Reset all global registries after each test.

    Some tests load custom units/substances/rates into the module-level
    registries; resetting keeps tests independent of execution order.
    """
    yield
    registry.reset()
    substance_registry.reset()
    inflation_registry.reset()
    exchange_rate_registry.reset()
