import numpy as np


class UnitRegistry:
    """Registry of units, dimensions, and conversion factors."""

    def __init__(self):
        """Initialize the unit registry with default units."""
        # Define dimensions for each unit
        self._dimensions = {
            # Energy
            "J": "ENERGY",
            "kJ": "ENERGY",
            "MJ": "ENERGY",
            "GJ": "ENERGY",
            "TJ": "ENERGY",
            "PJ": "ENERGY",
            "EJ": "ENERGY",
            "Wh": "ENERGY",
            "kWh": "ENERGY",
            "MWh": "ENERGY",
            "GWh": "ENERGY",
            "TWh": "ENERGY",
            "PWh": "ENERGY",
            "MMBTU": "ENERGY",

            # Power
            "W": "POWER",
            "kW": "POWER",
            "MW": "POWER",
            "GW": "POWER",
            "TW": "POWER",

            # Mass
            "g": "MASS",
            "kg": "MASS",
            "t": "MASS",
            "Mt": "MASS",
            "Gt": "MASS",

            # Volume
            "m3": "VOLUME",
            "L": "VOLUME",

            # Time
            "s": "TIME",
            "min": "TIME",
            "h": "TIME",
            "a": "TIME",
        }

        # Conversion factors to domain-appropriate base units
        self._conversion_factors = {
            # Energy (base: MWh)
            "J": 2.77778e-10,
            "kJ": 2.77778e-7,
            "MJ": 0.000277778,
            "GJ": 0.277778,
            "TJ": 277.778,
            "PJ": 277778.0,
            "EJ": 277778000.0,
            "Wh": 0.000001,
            "kWh": 0.001,
            "MWh": 1.0,
            "GWh": 1000.0,
            "TWh": 1000000.0,
            "PWh": 1000000000.0,
            "MMBTU": 0.293071,

            # Power (base: MW)
            "W": 0.000001,
            "kW": 0.001,
            "MW": 1.0,
            "GW": 1000.0,
            "TW": 1000000.0,

            # Mass (base: t)
            "g": 0.000001,
            "kg": 0.001,
            "t": 1.0,
            "Mt": 1000.0,
            "Gt": 1000000.0,

            # Volume (base: m3)
            "m3": 1.0,
            "L": 0.001,

            # Time (base: h)
            "s": 1 / 3600,
            "min": 1 / 60,
            "h": 1.0,
            "a": 8760,
        }

    def get_dimension(self, unit):
        """Get the dimension of a unit."""
        # Handle compound units
        if "/" in unit:
            numerator, denominator = unit.split("/", 1)
            return f"{self.get_dimension(numerator)}_PER_{self.get_dimension(denominator)}"

        if unit in self._dimensions:
            return self._dimensions[unit]

        raise ValueError(f"Unknown unit: {unit}")

    def get_conversion_factor(self, from_unit, to_unit):
        """Get conversion factor between compatible units."""
        # Check dimension compatibility
        if self.get_dimension(from_unit) != self.get_dimension(to_unit):
            raise ValueError(f"Incompatible units: {from_unit} and {to_unit}")

        # Handle compound units
        if "/" in from_unit and "/" in to_unit:
            from_num, from_den = from_unit.split("/", 1)
            to_num, to_den = to_unit.split("/", 1)

            num_factor = self.get_conversion_factor(from_num, to_num)
            den_factor = self.get_conversion_factor(from_den, to_den)

            return num_factor / den_factor

        # Simple units
        from_factor = self._conversion_factors.get(from_unit)
        to_factor = self._conversion_factors.get(to_unit)

        if from_factor is None or to_factor is None:
            raise ValueError(
                f"Conversion factor not defined for {from_unit} or {to_unit}")

        return from_factor / to_factor


# Create a global registry instance
registry = UnitRegistry()