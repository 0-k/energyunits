"""Unit registry with conversion logic."""

import json
from pathlib import Path
from typing import Optional


class UnitRegistry:
    """Registry of units, dimensions, and conversion factors."""

    def __init__(self):
        self._dimensions = {}
        self._conversion_factors = {}
        self._base_units = {}
        self._corresponding_units = {}
        self._dimensional_multiplication_rules = []
        self._dimensional_division_rules = []
        self._load_defaults()

    def _load_defaults(self):
        """Load default unit data from JSON."""
        data_path = Path(__file__).parent / "data" / "units.json"
        with open(data_path) as f:
            data = json.load(f)

        self._dimensions = data["dimensions"]
        self._conversion_factors = data["conversion_factors"]
        self._base_units = data["base_units"]
        self._corresponding_units = data["corresponding_units"]
        self._dimensional_multiplication_rules = data.get("dimensional_multiplication_rules", [])
        self._dimensional_division_rules = data.get("dimensional_division_rules", [])

    def load_units(self, file_path: str):
        """Load custom units from JSON file."""
        with open(file_path) as f:
            data = json.load(f)

        self._dimensions.update(data.get("dimensions", {}))
        self._conversion_factors.update(data.get("conversion_factors", {}))
        self._base_units.update(data.get("base_units", {}))
        self._corresponding_units.update(data.get("corresponding_units", {}))
        self._dimensional_multiplication_rules.extend(data.get("dimensional_multiplication_rules", []))
        self._dimensional_division_rules.extend(data.get("dimensional_division_rules", []))

    def get_dimension(self, unit: str) -> str:
        """Get dimension of a unit."""
        if unit == "":
            return "DIMENSIONLESS"

        if "/" in unit:
            numerator, denominator = unit.split("/", 1)
            num_dim = self.get_dimension(numerator)
            den_dim = self.get_dimension(denominator)

            if num_dim == "ENERGY" and den_dim == "TIME":
                return "POWER"

            return f"{num_dim}_PER_{den_dim}"

        if unit not in self._dimensions:
            raise ValueError(f"Unknown unit: {unit}")

        return self._dimensions[unit]

    def get_conversion_factor(self, from_unit: str, to_unit: str) -> float:
        """Get conversion factor between compatible units."""
        from_dim = self.get_dimension(from_unit)
        to_dim = self.get_dimension(to_unit)

        if from_dim != to_dim:
            raise ValueError(f"Incompatible units: {from_unit} and {to_unit}")

        if "/" in from_unit and "/" in to_unit:
            from_num, from_den = from_unit.split("/", 1)
            to_num, to_den = to_unit.split("/", 1)
            num_factor = self.get_conversion_factor(from_num, to_num)
            den_factor = self.get_conversion_factor(from_den, to_den)
            return num_factor / den_factor

        if "/" in from_unit or "/" in to_unit:
            return self._convert_compound_to_simple(from_unit, to_unit, from_dim)

        from_factor = self._conversion_factors.get(from_unit)
        to_factor = self._conversion_factors.get(to_unit)

        if from_factor is None or to_factor is None:
            raise ValueError(f"Conversion factor not defined for {from_unit} or {to_unit}")

        return from_factor / to_factor

    def are_dimensions_compatible(self, from_dim: str, to_dim: str) -> bool:
        """Check if dimensions can be converted."""
        if from_dim == to_dim:
            return True

        conversions = {
            ("ENERGY", "POWER"), ("POWER", "ENERGY"),
            ("MASS", "VOLUME"), ("VOLUME", "MASS"),
            ("MASS", "ENERGY"), ("ENERGY", "MASS"),
            ("ENERGY", "VOLUME"), ("VOLUME", "ENERGY"),
        }

        return (from_dim, to_dim) in conversions

    def convert_between_dimensions(self, value: float, from_unit: str, to_unit: str,
                                   substance: Optional[str] = None, **kwargs) -> float:
        """Convert between related dimensions."""
        from .substance import substance_registry

        from_dim = self.get_dimension(from_unit)
        to_dim = self.get_dimension(to_unit)

        # Mass ↔ Energy conversions
        if from_dim == "MASS" and to_dim == "ENERGY":
            if not substance:
                raise ValueError("Substance required for mass to energy conversion")

            mass_kg = value * self.get_conversion_factor(from_unit, "kg")
            mass_t = mass_kg / 1000

            basis = kwargs.get("basis", "LHV")
            heating_value_mj_kg = (substance_registry.hhv(substance) if basis.upper() == "HHV"
                                  else substance_registry.lhv(substance))
            heating_value_mwh_t = heating_value_mj_kg * 0.2778
            energy_mwh = mass_t * heating_value_mwh_t

            return energy_mwh * self.get_conversion_factor("MWh", to_unit)

        elif from_dim == "ENERGY" and to_dim == "MASS":
            if not substance:
                raise ValueError("Substance required for energy to mass conversion")

            energy_mwh = value * self.get_conversion_factor(from_unit, "MWh")

            basis = kwargs.get("basis", "LHV")
            heating_value_mj_kg = (substance_registry.hhv(substance) if basis.upper() == "HHV"
                                  else substance_registry.lhv(substance))
            heating_value_mwh_t = heating_value_mj_kg * 0.2778
            mass_t = energy_mwh / heating_value_mwh_t
            mass_kg = mass_t * 1000

            return mass_kg * self.get_conversion_factor("kg", to_unit)

        # Mass ↔ Volume conversions
        elif from_dim == "MASS" and to_dim == "VOLUME":
            if not substance:
                raise ValueError("Substance required for mass to volume conversion")

            density = substance_registry.density(substance)
            mass_kg = value * self.get_conversion_factor(from_unit, "kg")
            volume_m3 = mass_kg / density

            return volume_m3 * self.get_conversion_factor("m3", to_unit)

        elif from_dim == "VOLUME" and to_dim == "MASS":
            if not substance:
                raise ValueError("Substance required for volume to mass conversion")

            density = substance_registry.density(substance)
            volume_m3 = value * self.get_conversion_factor(from_unit, "m3")
            mass_kg = volume_m3 * density

            return mass_kg * self.get_conversion_factor("kg", to_unit)

        # Energy ↔ Volume (via mass)
        elif from_dim == "ENERGY" and to_dim == "VOLUME":
            if not substance:
                raise ValueError("Substance required for energy to volume conversion")

            mass_kg = self.convert_between_dimensions(value, from_unit, "kg", substance, **kwargs)
            return self.convert_between_dimensions(mass_kg, "kg", to_unit, substance, **kwargs)

        elif from_dim == "VOLUME" and to_dim == "ENERGY":
            if not substance:
                raise ValueError("Substance required for volume to energy conversion")

            mass_kg = self.convert_between_dimensions(value, from_unit, "kg", substance, **kwargs)
            return self.convert_between_dimensions(mass_kg, "kg", to_unit, substance, **kwargs)

        # Power ↔ Energy conversions
        elif from_dim == "POWER" and to_dim == "ENERGY":
            hours = kwargs.get("hours", 1.0)
            power_mw = value * self.get_conversion_factor(from_unit, "MW")
            energy_mwh = power_mw * hours
            return energy_mwh * self.get_conversion_factor("MWh", to_unit)

        elif from_dim == "ENERGY" and to_dim == "POWER":
            hours = kwargs.get("hours", 1.0)
            energy_mwh = value * self.get_conversion_factor(from_unit, "MWh")
            power_mw = energy_mwh / hours
            return power_mw * self.get_conversion_factor("MW", to_unit)

        raise ValueError(f"No conversion defined between {from_dim} and {to_dim}")

    def get_corresponding_unit(self, unit: str, target_dimension: str) -> str:
        """Get corresponding unit in another dimension (e.g., MW → MWh)."""
        if unit in self._corresponding_units:
            corresponding = self._corresponding_units[unit]
            if self.get_dimension(corresponding) == target_dimension:
                return corresponding

        raise ValueError(f"No corresponding {target_dimension} unit for {unit}")

    def get_multiplication_result(self, dim1: str, dim2: str) -> Optional[tuple]:
        """Get result dimension and source dimension from multiplying two dimensions.

        Returns: (result_dimension, source_dimension) or None
        Example: (POWER, TIME) -> ("ENERGY", "POWER")
        """
        for rule in self._dimensional_multiplication_rules:
            rule_dims = set(rule["dimensions"])
            if rule_dims == {dim1, dim2}:
                return (rule["result_dimension"], rule["source_dimension"])
        return None

    def get_division_result(self, numerator_dim: str, denominator_dim: str) -> Optional[str]:
        """Get result dimension from dividing two dimensions.

        Returns: result_dimension or None
        Example: (ENERGY, TIME) -> "POWER"
        """
        for rule in self._dimensional_division_rules:
            if (rule["numerator_dimension"] == numerator_dim and
                rule["denominator_dimension"] == denominator_dim):
                return rule["result_dimension"]
        return None

    def _convert_compound_to_simple(self, from_unit: str, to_unit: str, dimension: str) -> float:
        """Convert between compound and simple units."""
        if "/" in from_unit:
            compound_unit = from_unit
            simple_unit = to_unit
            is_from_compound = True
        else:
            compound_unit = to_unit
            simple_unit = from_unit
            is_from_compound = False

        if dimension == "POWER":
            num_unit, den_unit = compound_unit.split("/", 1)
            energy_factor = self.get_conversion_factor(num_unit, "MWh")
            time_factor = self.get_conversion_factor(den_unit, "h")
            compound_value_in_mw = energy_factor / time_factor
            mw_to_simple_factor = self.get_conversion_factor("MW", simple_unit)
            compound_to_simple_factor = compound_value_in_mw * mw_to_simple_factor
        else:
            raise ValueError(f"Compound to simple conversion not implemented for: {dimension}")

        return compound_to_simple_factor if is_from_compound else 1.0 / compound_to_simple_factor


registry = UnitRegistry()
