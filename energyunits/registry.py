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
            "barrel": "VOLUME",  # Oil barrel unit

            # Time
            "s": "TIME",
            "min": "TIME",
            "h": "TIME",
            "a": "TIME",

            # Currency
            "USD": "CURRENCY",
            "EUR": "CURRENCY",
            "GBP": "CURRENCY",
            "JPY": "CURRENCY",
            "CNY": "CURRENCY",
        }

        # Conversion factors to domain-appropriate base units
        self._conversion_factors = {
            # Energy (base: MWh)
            "J": 2.77778e-10,  # 1 J = 2.77778e-10 MWh
            "kJ": 2.77778e-7,  # 1 kJ = 2.77778e-7 MWh
            "MJ": 0.000277778,  # 1 MJ = 0.000277778 MWh
            "GJ": 0.277778,  # 1 GJ = 0.277778 MWh
            "TJ": 277.778,  # 1 TJ = 277.778 MWh
            "PJ": 277778.0,  # 1 PJ = 277,778 MWh
            "EJ": 277778000.0,  # 1 EJ = 277,778,000 MWh
            "Wh": 0.000001,  # 1 Wh = 0.000001 MWh
            "kWh": 0.001,  # 1 kWh = 0.001 MWh
            "MWh": 1.0,  # 1 MWh = 1.0 MWh
            "GWh": 1000.0,  # 1 GWh = 1,000 MWh
            "TWh": 1000000.0,  # 1 TWh = 1,000,000 MWh
            "PWh": 1000000000.0,  # 1 PWh = 1,000,000,000 MWh
            "MMBTU": 0.293071,  # 1 MMBTU = 0.293071 MWh

            # Power (base: MW)
            "W": 0.000001,  # 1 W = 0.000001 MW
            "kW": 0.001,  # 1 kW = 0.001 MW
            "MW": 1.0,  # 1 MW = 1.0 MW
            "GW": 1000.0,  # 1 GW = 1,000 MW
            "TW": 1000000.0,  # 1 TW = 1,000,000 MW

            # Mass (base: t)
            "g": 0.000001,  # 1 g = 0.000001 t
            "kg": 0.001,  # 1 kg = 0.001 t
            "t": 1.0,  # 1 t = 1.0 t
            "Mt": 1000000.0,  # 1 Mt = 1,000,000 t
            "Gt": 1000000000.0,  # 1 Gt = 1,000,000,000 t

            # Volume (base: m3)
            "m3": 1.0,  # 1 m3 = 1.0 m3
            "L": 0.001,  # 1 L = 0.001 m3
            "barrel": 0.159,  # 1 barrel = 0.159 m3 (oil barrel)

            # Time (base: h)
            "s": 1 / 3600,  # 1 s = 1/3600 h
            "min": 1 / 60,  # 1 min = 1/60 h
            "h": 1.0,  # 1 h = 1.0 h
            "a": 8760,  # 1 a (year) = 8760 h

            # Currency (base: USD)
            "USD": 1.0,  # 1 USD = 1.0 USD
            "EUR": 1.08,  # 1 EUR = 1.08 USD (approximate)
            "GBP": 1.27,  # 1 GBP = 1.27 USD (approximate)
            "JPY": 0.0067,  # 1 JPY = 0.0067 USD (approximate)
            "CNY": 0.14,  # 1 CNY = 0.14 USD (approximate)
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