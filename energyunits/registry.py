"""
Enhanced unit registry with improved conversion logic and dimension relationships.
"""

import numpy as np
from typing import Dict, Tuple, Optional, Callable, Any


class UnitRegistry:
    """Registry of units, dimensions, and conversion factors with improved architecture."""

    def __init__(self):
        """Initialize the unit registry with default units and dimension relationships."""
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
            "barrel": "VOLUME",

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
            "J": 2.77778e-10,      # 1 J = 2.77778e-10 MWh
            "kJ": 2.77778e-7,      # 1 kJ = 2.77778e-7 MWh
            "MJ": 0.000277778,     # 1 MJ = 0.000277778 MWh
            "GJ": 0.277778,        # 1 GJ = 0.277778 MWh
            "TJ": 277.778,         # 1 TJ = 277.778 MWh
            "PJ": 277778.0,        # 1 PJ = 277,778 MWh
            "EJ": 277778000.0,     # 1 EJ = 277,778,000 MWh
            "Wh": 0.000001,        # 1 Wh = 0.000001 MWh
            "kWh": 0.001,          # 1 kWh = 0.001 MWh
            "MWh": 1.0,            # 1 MWh = 1.0 MWh
            "GWh": 1000.0,         # 1 GWh = 1,000 MWh
            "TWh": 1000000.0,      # 1 TWh = 1,000,000 MWh
            "PWh": 1000000000.0,   # 1 PWh = 1,000,000,000 MWh
            "MMBTU": 0.293071,     # 1 MMBTU = 0.293071 MWh

            # Power (base: MW)
            "W": 0.000001,         # 1 W = 0.000001 MW
            "kW": 0.001,           # 1 kW = 0.001 MW
            "MW": 1.0,             # 1 MW = 1.0 MW
            "GW": 1000.0,          # 1 GW = 1,000 MW
            "TW": 1000000.0,       # 1 TW = 1,000,000 MW

            # Mass (base: t)
            "g": 0.000001,         # 1 g = 0.000001 t
            "kg": 0.001,           # 1 kg = 0.001 t
            "t": 1.0,              # 1 t = 1.0 t
            "Mt": 1000000.0,       # 1 Mt = 1,000,000 t
            "Gt": 1000000000.0,    # 1 Gt = 1,000,000,000 t

            # Volume (base: m3)
            "m3": 1.0,             # 1 m3 = 1.0 m3
            "L": 0.001,            # 1 L = 0.001 m3
            "barrel": 0.159,       # 1 barrel = 0.159 m3 (oil barrel)

            # Time (base: h)
            "s": 1 / 3600,         # 1 s = 1/3600 h
            "min": 1 / 60,         # 1 min = 1/60 h
            "h": 1.0,              # 1 h = 1.0 h
            "a": 8760,             # 1 a (year) = 8760 h

            # Currency (base: USD)
            "USD": 1.0,            # 1 USD = 1.0 USD
            "EUR": 1.08,           # 1 EUR = 1.08 USD (approximate)
            "GBP": 1.27,           # 1 GBP = 1.27 USD (approximate)
            "JPY": 0.0067,         # 1 JPY = 0.0067 USD (approximate)
            "CNY": 0.14,           # 1 CNY = 0.14 USD (approximate)
        }

        # Define relationships between dimensions
        self._dimension_relationships = {
            # Energy to Power
            ("ENERGY", "POWER"): self._energy_to_power,

            # Power to Energy
            ("POWER", "ENERGY"): self._power_to_energy,

            # Mass to Volume (requires substance properties)
            ("MASS", "VOLUME"): self._mass_to_volume,

            # Volume to Mass (requires substance properties)
            ("VOLUME", "MASS"): self._volume_to_mass,
        }

        # Map standard unit pairs for dimension relationships
        self._standard_unit_pairs = {
            ("ENERGY", "POWER"): ("MWh", "MW"),
            ("POWER", "ENERGY"): ("MW", "MWh"),
            ("MASS", "VOLUME"): ("kg", "m3"),
            ("VOLUME", "MASS"): ("m3", "kg"),
        }

        # Map for corresponding units (e.g., MW → MWh, W → Wh)
        self._corresponding_units = {
            # Power to Energy
            "W": "Wh",
            "kW": "kWh",
            "MW": "MWh",
            "GW": "GWh",
            "TW": "TWh",

            # Energy to Power
            "Wh": "W",
            "kWh": "kW",
            "MWh": "MW",
            "GWh": "GW",
            "TWh": "TW",
        }

    def get_dimension(self, unit: str) -> str:
        """Get the dimension of a unit with improved handling of compound units."""
        # Handle compound units
        if "/" in unit:
            numerator, denominator = unit.split("/", 1)
            return f"{self.get_dimension(numerator)}_PER_{self.get_dimension(denominator)}"

        if unit in self._dimensions:
            return self._dimensions[unit]

        raise ValueError(f"Unknown unit: {unit}")

    def are_dimensions_compatible(self, from_dim: str, to_dim: str) -> bool:
        """Check if two dimensions are directly compatible or can be converted."""
        # Same dimension is always compatible
        if from_dim == to_dim:
            return True

        # Check if there's a defined relationship between dimensions
        if (from_dim, to_dim) in self._dimension_relationships:
            return True

        return False

    def convert_between_dimensions(self, value: float, from_unit: str, to_unit: str,
                                  substance: Optional[str] = None, **kwargs) -> float:
        """Convert a value between different but related dimensions.

        Args:
            value: The value to convert
            from_unit: Source unit
            to_unit: Target unit
            substance: Optional substance for substance-specific conversions
            **kwargs: Additional parameters for specific conversions

        Returns:
            Converted value
        """
        from_dim = self.get_dimension(from_unit)
        to_dim = self.get_dimension(to_unit)

        # Find the conversion relationship
        if (from_dim, to_dim) in self._dimension_relationships:
            converter = self._dimension_relationships[(from_dim, to_dim)]
            # Call the conversion function with all parameters
            return converter(value, from_unit, to_unit, substance, **kwargs)

        raise ValueError(f"No conversion defined between {from_dim} and {to_dim}")

    def _energy_to_power(self, value: float, from_unit: str, to_unit: str,
                        substance: Optional[str] = None, hours: float = 1.0, **kwargs) -> float:
        """Convert energy to power by dividing by time (default = 1 hour)."""
        # Convert to standard units first (MWh)
        energy_mwh = value * self.get_conversion_factor(from_unit, "MWh")

        # Divide by hours to get power in MW
        power_mw = energy_mwh / hours

        # Convert from MW to the target power unit
        return power_mw * self.get_conversion_factor("MW", to_unit)

    def _power_to_energy(self, value: float, from_unit: str, to_unit: str,
                         substance: Optional[str] = None, hours: float = 1.0, **kwargs) -> float:
        """Convert power to energy by multiplying by time (default = 1 hour)."""
        # Convert to standard units first (MW)
        power_mw = value * self.get_conversion_factor(from_unit, "MW")

        # Multiply by hours to get energy in MWh
        energy_mwh = power_mw * hours

        # Convert from MWh to the target energy unit
        return energy_mwh * self.get_conversion_factor("MWh", to_unit)

    def _mass_to_volume(self, value: float, from_unit: str, to_unit: str,
                        substance: Optional[str] = None, **kwargs) -> float:
        """Convert mass to volume using substance density."""
        # This requires the substance registry
        from .substance import substance_registry

        if substance is None:
            raise ValueError("Substance must be specified for mass to volume conversion")

        # Get substance density (kg/m3)
        density = substance_registry.get_density(substance)

        # Convert to kg first
        mass_kg = value * self.get_conversion_factor(from_unit, "kg")

        # Calculate volume in m3
        volume_m3 = mass_kg / density

        # Convert to target volume unit
        return volume_m3 * self.get_conversion_factor("m3", to_unit)

    def _volume_to_mass(self, value: float, from_unit: str, to_unit: str,
                        substance: Optional[str] = None, **kwargs) -> float:
        """Convert volume to mass using substance density."""
        # This requires the substance registry
        from .substance import substance_registry

        if substance is None:
            raise ValueError("Substance must be specified for volume to mass conversion")

        # Get substance density (kg/m3)
        density = substance_registry.get_density(substance)

        # Convert to m3 first
        volume_m3 = value * self.get_conversion_factor(from_unit, "m3")

        # Calculate mass in kg
        mass_kg = volume_m3 * density

        # Convert to target mass unit
        return mass_kg * self.get_conversion_factor("kg", to_unit)

    def get_conversion_factor(self, from_unit: str, to_unit: str) -> float:
        """Get conversion factor between compatible units."""
        # Check dimension compatibility
        from_dim = self.get_dimension(from_unit)
        to_dim = self.get_dimension(to_unit)

        if from_dim != to_dim:
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

    def get_corresponding_unit(self, unit: str, target_dimension: str) -> str:
        """Get the corresponding unit in another dimension (e.g., MW → MWh)."""
        if unit in self._corresponding_units:
            corresponding = self._corresponding_units[unit]
            if self.get_dimension(corresponding) == target_dimension:
                return corresponding

        # Fallback to standard units for the dimensions
        from_dim = self.get_dimension(unit)
        if (from_dim, target_dimension) in self._standard_unit_pairs:
            _, standard_to = self._standard_unit_pairs[(from_dim, target_dimension)]
            return standard_to

        raise ValueError(f"No corresponding {target_dimension} unit for {unit}")


# Create a global registry instance
registry = UnitRegistry()