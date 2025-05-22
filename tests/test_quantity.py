"""
Unit tests for the Quantity class.

These tests focus on Quantity operations such as arithmetic,
conversions, and special methods.
"""

import numpy as np
import pytest

from energyunits import Quantity


class TestQuantityBasics:
    def test_initialization(self):
        """Test initializing Quantity objects."""
        # Basic initialization
        q = Quantity(100, "MWh")
        assert q.value == 100
        assert q.unit == "MWh"
        assert q.dimension == "ENERGY"
        assert q.substance is None
        assert q.basis is None
        assert q.reference_year is None

        # With substance
        q = Quantity(100, "t", "coal")
        assert q.substance == "coal"

        # With basis
        q = Quantity(100, "MWh", "natural_gas", "HHV")
        assert q.basis == "HHV"

        # With reference year
        q = Quantity(100, "USD/kW", reference_year=2020)
        assert q.reference_year == 2020

        # With array value
        q = Quantity([1, 2, 3], "MW")
        assert np.all(q.value == np.array([1, 2, 3]))

    def test_string_representation(self):
        """Test string and repr methods."""
        # Simple case
        q = Quantity(100, "MWh")
        assert str(q) == "100 MWh"

        # With substance
        q = Quantity(100, "t", "coal")
        assert str(q) == "100 t of coal"

        # Repr should include more details
        q = Quantity(100, "MWh", "natural_gas", "HHV", 2020)
        repr_str = repr(q)
        assert "Quantity" in repr_str
        assert "100" in repr_str
        assert "MWh" in repr_str
        assert "natural_gas" in repr_str
        assert "HHV" in repr_str
        assert "2020" in repr_str


class TestQuantityOperations:
    def test_basic_conversion(self):
        """Test basic unit conversions."""
        # Energy conversion
        energy = Quantity(100, "MWh")
        energy_gj = energy.to("GJ")
        assert energy_gj.value == pytest.approx(360)
        assert energy_gj.unit == "GJ"

        # Power conversion
        power = Quantity(50, "MW")
        power_kw = power.to("kW")
        assert power_kw.value == pytest.approx(50000)
        assert power_kw.unit == "kW"

        # Mass conversion
        mass = Quantity(1, "t")
        mass_kg = mass.to("kg")
        assert mass_kg.value == pytest.approx(1000)
        assert mass_kg.unit == "kg"

    def test_array_operations(self):
        """Test operations with array values."""
        # Array conversion
        energy = Quantity([100, 200, 300], "MWh")
        energy_gj = energy.to("GJ")
        assert np.all(energy_gj.value == pytest.approx([360, 720, 1080]))

        # Array multiplication
        energy = Quantity([100, 200, 300], "MWh")
        doubled = energy * 2
        assert np.all(doubled.value == pytest.approx([200, 400, 600]))

        # Array division
        energy = Quantity([100, 200, 300], "MWh")
        halved = energy / 2
        assert np.all(halved.value == pytest.approx([50, 100, 150]))

        # Array addition
        energy1 = Quantity([100, 200, 300], "MWh")
        energy2 = Quantity([50, 50, 50], "MWh")
        total = energy1 + energy2
        assert np.all(total.value == pytest.approx([150, 250, 350]))

    def test_arithmetic_operations(self):
        """Test arithmetic operations between quantities."""
        # Addition with same units
        energy1 = Quantity(100, "MWh")
        energy2 = Quantity(50, "MWh")
        total = energy1 + energy2
        assert total.value == pytest.approx(150)
        assert total.unit == "MWh"

        # Addition with different units
        energy1 = Quantity(100, "MWh")
        energy2 = Quantity(360, "GJ")  # 100 MWh
        total = energy1 + energy2
        assert total.value == pytest.approx(200)
        assert total.unit == "MWh"

        # Addition clears substance if different
        energy1 = Quantity(100, "MWh", "coal")
        energy2 = Quantity(100, "MWh", "natural_gas")
        total = energy1 + energy2
        assert total.substance is None

        # Addition clears basis if different
        energy1 = Quantity(100, "MWh", "natural_gas", "HHV")
        energy2 = Quantity(100, "MWh", "natural_gas", "LHV")
        total = energy1 + energy2
        assert total.basis is None

        # Multiplication by scalar
        energy = Quantity(100, "MWh")
        doubled = energy * 2
        assert doubled.value == pytest.approx(200)
        assert doubled.unit == "MWh"

        # Right multiplication by scalar
        energy = Quantity(100, "MWh")
        doubled = 2 * energy
        assert doubled.value == pytest.approx(200)
        assert doubled.unit == "MWh"

        # Division by scalar
        energy = Quantity(100, "MWh")
        halved = energy / 2
        assert halved.value == pytest.approx(50)
        assert halved.unit == "MWh"

    def test_special_divisions(self):
        """Test special division cases."""
        # Energy / time = power
        energy = Quantity(100, "MWh")
        time = Quantity(10, "h")
        power = energy / time
        assert power.value == pytest.approx(10)
        assert power.unit == "MW"

        # With different energy units
        energy = Quantity(3600, "GJ")  # 1000 MWh
        time = Quantity(10, "h")
        power = energy / time
        assert power.value == pytest.approx(100)
        assert power.unit == "MW"

        # With different time units
        energy = Quantity(100, "MWh")
        time = Quantity(600, "min")  # 10 h
        power = energy / time
        assert power.value == pytest.approx(10)
        assert power.unit == "MW"

        # General case - creates compound unit
        mass = Quantity(100, "t")
        volume = Quantity(50, "m3")
        density = mass / volume
        assert density.value == pytest.approx(2)
        assert density.unit == "t/m3"

    def test_comparison_operations(self):
        """Test comparison operators."""
        energy_small = Quantity(100, "MWh")
        energy_large = Quantity(200, "MWh")

        # Less than
        assert energy_small < energy_large
        assert not energy_large < energy_small

        # Greater than
        assert energy_large > energy_small
        assert not energy_small > energy_large

        # Less than or equal
        assert energy_small <= energy_large
        assert energy_small <= Quantity(100, "MWh")
        assert not energy_large <= energy_small

        # Greater than or equal
        assert energy_large >= energy_small
        assert energy_large >= Quantity(200, "MWh")
        assert not energy_small >= energy_large

        # Equal
        assert energy_small == Quantity(100, "MWh")
        assert not energy_small == energy_large

        # Not equal
        assert energy_small != energy_large
        assert not energy_small != Quantity(100, "MWh")

        # Different units
        assert Quantity(1, "MWh") > Quantity(1, "kWh")
        assert Quantity(1, "GJ") < Quantity(1, "MWh")  # 1 MWh ≈ 3.6 GJ

    def test_dimension_conversions(self):
        """Test conversions between related dimensions."""
        # Power to energy
        power = Quantity(10, "MW")
        energy = power.for_duration(hours=5)
        assert energy.value == pytest.approx(50)
        assert energy.unit == "MWh"

        # Energy to power
        energy = Quantity(240, "MWh")
        power = energy.average_power(hours=12)
        assert power.value == pytest.approx(20)
        assert power.unit == "MW"

        # Mass to volume (substance-specific)
        lng_mass = Quantity(450, "kg", "lng")
        lng_volume = lng_mass.to("m3")
        assert lng_volume.value == pytest.approx(1.0, rel=0.1)
        assert lng_volume.unit == "m3"

        # Volume to mass (substance-specific)
        oil_volume = Quantity(1, "barrel", "oil")
        oil_mass = oil_volume.to("kg")
        assert oil_mass.unit == "kg"
        # The value will depend on oil density
