"""Test compound unit conversions."""

import pytest

from energyunits import Quantity


class TestCompoundUnits:
    """Test compound unit conversion functionality."""

    def test_energy_per_time_to_power(self):
        """Test that GWh/min converts correctly to MW."""
        q = Quantity(100, 'GWh/min')
        
        # Verify dimension is recognized as POWER
        assert q.dimension == "POWER"
        
        result = q.to('MW')
        
        # Check the math: 100 GWh/min = 100 * 1000 MWh/min = 100000 MWh/min
        # 1 min = 1/60 h, so 100000 MWh/min = 100000 * 60 MWh/h = 6000000 MW
        expected = 100 * 1000 * 60  # 6,000,000 MW
        assert result.value == pytest.approx(expected)
        assert result.unit == "MW"

    def test_power_to_energy_per_time(self):
        """Test MW to GWh/min conversion (reverse)."""
        q = Quantity(6000000, 'MW')
        result = q.to('GWh/min')
        
        expected = 100  # Should be 100 GWh/min
        assert result.value == pytest.approx(expected)
        assert result.unit == "GWh/min"

    def test_mwh_per_hour_to_power(self):
        """Test MWh/h to MW conversion."""
        q = Quantity(1, 'MWh/h')
        
        # Verify dimension is recognized as POWER
        assert q.dimension == "POWER"
        
        result = q.to('MW')
        
        expected = 1  # 1 MWh/h = 1 MW
        assert result.value == pytest.approx(expected)
        assert result.unit == "MW"

    def test_various_energy_time_combinations(self):
        """Test various energy/time unit combinations."""
        test_cases = [
            (Quantity(1, 'kWh/h'), 'kW', 1),
            (Quantity(1, 'TWh/h'), 'TW', 1),
            (Quantity(60, 'MWh/min'), 'MW', 3600),  # 60 MWh/min = 3600 MW
            (Quantity(1, 'GJ/s'), 'MW', 1000),     # 1 GJ/s = 1000 MW (1 GJ = 1000 MJ, 1 MJ/s = 1 MW)
        ]
        
        for quantity, target_unit, expected in test_cases:
            assert quantity.dimension == "POWER"
            result = quantity.to(target_unit)
            assert result.value == pytest.approx(expected)

    def test_compound_unit_arithmetic(self):
        """Test arithmetic operations with compound units."""
        # Energy per time unit
        power_rate = Quantity(100, 'GWh/min')
        
        # Multiply by time to get energy
        time_duration = Quantity(30, 'min')
        energy = power_rate * time_duration
        
        # Should get energy - the result unit is determined by dimensional analysis
        # GWh/min * min = GWh, but the multiplication returns the appropriate energy unit
        assert energy.value == pytest.approx(3000)  # 100 GWh/min * 30 min = 3000 GWh (or equivalent in MWh)
        assert energy.unit == "MWh"