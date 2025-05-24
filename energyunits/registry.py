"""
Enhanced unit registry with improved conversion logic and dimension relationships.
"""

from typing import Any, Callable, Dict, Optional


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
            "J": 1e-9 / 3.6,
            "kJ": 1e-6 / 3.6,
            "MJ": 1e-3 / 3.6,
            "GJ": 1 / 3.6,
            "TJ": 1e3 / 3.6,
            "PJ": 1e6 / 3.6,
            "EJ": 1e9 / 3.6,
            "Wh": 1e-6,
            "kWh": 1e-3,  # 1 kWh = 0.001 MWh
            "MWh": 1,  # 1 MWh = 1.0 MWh
            "GWh": 1e3,  # 1 GWh = 1,000 MWh
            "TWh": 1e6,  # 1 TWh = 1,000,000 MWh
            "PWh": 1e9,  # 1 PWh = 1,000,000,000 MWh
            "MMBTU": 0.293071,  # 1 MMBTU = 0.293071 MWh
            # Power (base: MW)
            "W": 1e-6,  # 1 W = 0.000001 MW
            "kW": 1e-3,  # 1 kW = 0.001 MW
            "MW": 1,  # 1 MW = 1.0 MW
            "GW": 1e3,  # 1 GW = 1,000 MW
            "TW": 1e6,  # 1 TW = 1,000,000 MW
            # Mass (base: t)
            "g": 1e-6,  # 1 g = 0.000001 t
            "kg": 1e-3,  # 1 kg = 0.001 t
            "t": 1,  # 1 t = 1.0 t
            "Mt": 1e6,  # 1 Mt = 1,000,000 t
            "Gt": 1e9,  # 1 Gt = 1,000,000,000 t
            # Volume (base: m3)
            "m3": 1,  # 1 m3 = 1.0 m3
            "L": 1e-3,  # 1 L = 0.001 m3
            "barrel": 0.159,  # 1 barrel = 0.159 m3 (oil barrel)
            # Time (base: h)
            "s": 1 / 3600,  # 1 s = 1/3600 h
            "min": 1 / 60,  # 1 min = 1/60 h
            "h": 1,  # 1 h = 1.0 h
            "a": 8760,  # 1 a (year) = 8760 h
            # Currency (base: USD)
            "USD": 1,  # 1 USD = 1.0 USD
            "EUR": 1.08,  # 1 EUR = 1.08 USD (approximate)
            "GBP": 1.27,  # 1 GBP = 1.27 USD (approximate)
            "JPY": 0.0067,  # 1 JPY = 0.0067 USD (approximate)
            "CNY": 0.14,  # 1 CNY = 0.14 USD (approximate)
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
            # Energy to Mass (requires substance properties)
            ("ENERGY", "MASS"): self._energy_to_mass,
            # Mass to Energy (requires substance properties)
            ("MASS", "ENERGY"): self._mass_to_energy,
            # Energy to Volume (requires substance properties)
            ("ENERGY", "VOLUME"): self._energy_to_volume,
            # Volume to Energy (requires substance properties)
            ("VOLUME", "ENERGY"): self._volume_to_energy,
        }

        # Map standard unit pairs for dimension relationships
        self._standard_unit_pairs = {
            ("ENERGY", "POWER"): ("MWh", "MW"),
            ("POWER", "ENERGY"): ("MW", "MWh"),
            ("MASS", "VOLUME"): ("kg", "m3"),
            ("VOLUME", "MASS"): ("m3", "kg"),
            ("ENERGY", "MASS"): ("MWh", "kg"),
            ("MASS", "ENERGY"): ("kg", "MWh"),
            ("ENERGY", "VOLUME"): ("MWh", "m3"),
            ("VOLUME", "ENERGY"): ("m3", "MWh"),
        }

        # Define base units for each dimension
        self._base_units = {
            "ENERGY": "MWh",
            "POWER": "MW",
            "MASS": "t",
            "VOLUME": "m3",
            "TIME": "h",
            "CURRENCY": "USD",
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
        # Handle dimensionless (empty string)
        if unit == "":
            return "DIMENSIONLESS"

        # Handle compound units
        if "/" in unit:
            numerator, denominator = unit.split("/", 1)
            num_dim = self.get_dimension(numerator)
            den_dim = self.get_dimension(denominator)

            # Normalize compound dimensions to fundamental equivalents
            if num_dim == "ENERGY" and den_dim == "TIME":
                return "POWER"

            return f"{num_dim}_PER_{den_dim}"

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

    def convert_between_dimensions(
        self,
        value: float,
        from_unit: str,
        to_unit: str,
        substance: Optional[str] = None,
        **kwargs,
    ) -> float:
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

    def _energy_to_power(
        self,
        value: float,
        from_unit: str,
        to_unit: str,
        substance: Optional[str] = None,
        hours: float = 1.0,
        **kwargs,
    ) -> float:
        """Convert energy to power by dividing by time (default = 1 hour)."""
        # Convert to standard units first (MWh)
        energy_mwh = value * self.get_conversion_factor(from_unit, "MWh")

        # Divide by hours to get power in MW
        power_mw = energy_mwh / hours

        # Convert from MW to the target power unit
        return power_mw * self.get_conversion_factor("MW", to_unit)

    def _power_to_energy(
        self,
        value: float,
        from_unit: str,
        to_unit: str,
        substance: Optional[str] = None,
        hours: float = 1.0,
        **kwargs,
    ) -> float:
        """Convert power to energy by multiplying by time (default = 1 hour)."""
        # Convert to standard units first (MW)
        power_mw = value * self.get_conversion_factor(from_unit, "MW")

        # Multiply by hours to get energy in MWh
        energy_mwh = power_mw * hours

        # Convert from MWh to the target energy unit
        return energy_mwh * self.get_conversion_factor("MWh", to_unit)

    def _mass_to_volume(
        self,
        value: float,
        from_unit: str,
        to_unit: str,
        substance: Optional[str] = None,
        **kwargs,
    ) -> float:
        """Convert mass to volume using substance density."""
        from .substance import substance_registry

        if substance is None:
            raise ValueError(
                "Substance must be specified for mass to volume conversion"
            )

        # Get substance density (kg/m3)
        density = substance_registry.density(substance)

        # Convert to kg first
        mass_kg = value * self.get_conversion_factor(from_unit, "kg")

        # Calculate volume in m3
        volume_m3 = mass_kg / density

        # Convert to target volume unit
        return volume_m3 * self.get_conversion_factor("m3", to_unit)

    def _volume_to_mass(
        self,
        value: float,
        from_unit: str,
        to_unit: str,
        substance: Optional[str] = None,
        **kwargs,
    ) -> float:
        """Convert volume to mass using substance density."""
        from .substance import substance_registry

        if substance is None:
            raise ValueError(
                "Substance must be specified for volume to mass conversion"
            )

        # Get substance density (kg/m3)
        density = substance_registry.density(substance)

        # Convert to m3 first
        volume_m3 = value * self.get_conversion_factor(from_unit, "m3")

        # Calculate mass in kg
        mass_kg = volume_m3 * density

        # Convert to target mass unit
        return mass_kg * self.get_conversion_factor("kg", to_unit)

    def _energy_to_mass(
        self,
        value: float,
        from_unit: str,
        to_unit: str,
        substance: Optional[str] = None,
        **kwargs,
    ) -> float:
        """Convert energy to mass using substance heating value."""
        from .substance import substance_registry

        if substance is None:
            raise ValueError(
                "Substance must be specified for energy to mass conversion"
            )

        # Convert energy to MWh first
        energy_mwh = value * self.get_conversion_factor(from_unit, "MWh")

        # Get heating value in MJ/kg and convert to MWh/t
        basis = kwargs.get("basis", "LHV")
        if basis.upper() == "HHV":
            heating_value_mj_kg = substance_registry.hhv(substance)
        else:
            heating_value_mj_kg = substance_registry.lhv(substance)

        # Convert MJ/kg to MWh/t: MJ/kg * 0.2778 MWh/MJ * 1000 kg/t = 277.8 MWh/t
        heating_value_mwh_t = heating_value_mj_kg * 0.2778

        # Calculate mass in tonnes
        mass_t = energy_mwh / heating_value_mwh_t

        # Convert to kg
        mass_kg = mass_t * 1000

        # Convert to target mass unit
        return mass_kg * self.get_conversion_factor("kg", to_unit)

    def _mass_to_energy(
        self,
        value: float,
        from_unit: str,
        to_unit: str,
        substance: Optional[str] = None,
        **kwargs,
    ) -> float:
        """Convert mass to energy using substance heating value."""
        from .substance import substance_registry

        if substance is None:
            raise ValueError(
                "Substance must be specified for mass to energy conversion"
            )

        # Convert to kg first
        mass_kg = value * self.get_conversion_factor(from_unit, "kg")

        # Convert to tonnes
        mass_t = mass_kg / 1000

        # Get heating value in MJ/kg and convert to MWh/t
        basis = kwargs.get("basis", "LHV")
        if basis.upper() == "HHV":
            heating_value_mj_kg = substance_registry.hhv(substance)
        else:
            heating_value_mj_kg = substance_registry.lhv(substance)

        # Convert MJ/kg to MWh/t: MJ/kg * 0.2778 MWh/MJ * 1000 kg/t = 277.8 MWh/t
        heating_value_mwh_t = heating_value_mj_kg * 0.2778

        # Calculate energy in MWh
        energy_mwh = mass_t * heating_value_mwh_t

        # Convert to target energy unit
        return energy_mwh * self.get_conversion_factor("MWh", to_unit)

    def _energy_to_volume(
        self,
        value: float,
        from_unit: str,
        to_unit: str,
        substance: Optional[str] = None,
        **kwargs,
    ) -> float:
        """Convert energy to volume via mass (energy → mass → volume)."""
        if substance is None:
            raise ValueError(
                "Substance must be specified for energy to volume conversion"
            )

        # First convert energy to mass
        mass_kg = self._energy_to_mass(value, from_unit, "kg", substance, **kwargs)

        # Then convert mass to volume
        return self._mass_to_volume(mass_kg, "kg", to_unit, substance, **kwargs)

    def _volume_to_energy(
        self,
        value: float,
        from_unit: str,
        to_unit: str,
        substance: Optional[str] = None,
        **kwargs,
    ) -> float:
        """Convert volume to energy via mass (volume → mass → energy)."""
        if substance is None:
            raise ValueError(
                "Substance must be specified for volume to energy conversion"
            )

        # First convert volume to mass
        mass_kg = self._volume_to_mass(value, from_unit, "kg", substance, **kwargs)

        # Then convert mass to energy
        return self._mass_to_energy(mass_kg, "kg", to_unit, substance, **kwargs)

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

        # Handle compound unit to simple unit (or vice versa)
        if "/" in from_unit or "/" in to_unit:
            return self._convert_compound_to_simple(from_unit, to_unit, from_dim)

        # Simple units
        from_factor = self._conversion_factors.get(from_unit)
        to_factor = self._conversion_factors.get(to_unit)

        if from_factor is None or to_factor is None:
            raise ValueError(
                f"Conversion factor not defined for {from_unit} or {to_unit}"
            )

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

    def _convert_compound_to_simple(
        self, from_unit: str, to_unit: str, dimension: str
    ) -> float:
        """Convert between compound and simple units of the same fundamental dimension."""
        # Determine which is compound and which is simple
        if "/" in from_unit:
            compound_unit = from_unit
            simple_unit = to_unit
            is_from_compound = True
        else:
            compound_unit = to_unit
            simple_unit = from_unit
            is_from_compound = False

        # Calculate the value of the compound unit in base units
        if dimension == "POWER":
            # For ENERGY/TIME -> POWER conversions
            num_unit, den_unit = compound_unit.split("/", 1)

            # Convert numerator to base energy unit (MWh)
            energy_factor = self.get_conversion_factor(num_unit, "MWh")

            # Convert denominator to base time unit (h)
            time_factor = self.get_conversion_factor(den_unit, "h")

            # Calculate compound unit value: energy_factor / time_factor gives MW
            compound_value_in_mw = energy_factor / time_factor

            # Convert from MW to target simple unit
            mw_to_simple_factor = self.get_conversion_factor("MW", simple_unit)
            compound_to_simple_factor = compound_value_in_mw * mw_to_simple_factor

        else:
            raise ValueError(
                f"Compound to simple conversion not implemented for dimension: {dimension}"
            )

        # Return the conversion factor in the correct direction
        if is_from_compound:
            return compound_to_simple_factor
        else:
            return 1.0 / compound_to_simple_factor

    def add_unit(self, unit: str, dimension: str, conversion_factor: float) -> None:
        """
        Add a new unit to the registry at runtime.

        Args:
            unit: Unit symbol (e.g., "hp", "BTU")
            dimension: Physical dimension (e.g., "POWER", "ENERGY")
            conversion_factor: Factor to convert TO base unit (unit * factor = base_unit)

        Examples:
            >>> registry.add_unit("hp", "POWER", 0.000746)  # 1 hp = 0.000746 MW
            >>> registry.add_unit("BTU", "ENERGY", 0.0002931)  # 1 BTU ≈ 0.0002931 MWh
        """
        # Validate dimension exists or add it
        if dimension not in self._base_units:
            # For custom dimensions, use first unit as base
            self._base_units[dimension] = unit
            # Set factor to 1.0 for new base unit
            if unit not in self._conversion_factors:
                conversion_factor = 1.0

        # Add to dimensions registry
        self._dimensions[unit] = dimension

        # Add conversion factor
        self._conversion_factors[unit] = conversion_factor

    def add_unit_with_reference(
        self, unit: str, dimension: str, reference_value: float, reference_unit: str
    ) -> None:
        """
        Add a new unit by specifying its value relative to an existing unit.

        Args:
            unit: New unit symbol
            dimension: Physical dimension
            reference_value: How many reference units equal 1 new unit
            reference_unit: Existing unit to reference

        Examples:
            >>> registry.add_unit_with_reference("hp", "POWER", 0.746, "kW")  # 1 hp = 0.746 kW
            >>> registry.add_unit_with_reference("therm", "ENERGY", 105.5, "MJ")  # 1 therm = 105.5 MJ
        """
        # Get conversion factor for reference unit
        if reference_unit not in self._conversion_factors:
            raise ValueError(f"Reference unit '{reference_unit}' not found in registry")

        reference_factor = self._conversion_factors[reference_unit]

        # Calculate conversion factor: new_unit * factor = base_unit
        # 1 new_unit = reference_value * reference_unit
        # 1 new_unit = reference_value * reference_factor * base_unit
        conversion_factor = reference_value * reference_factor

        self.add_unit(unit, dimension, conversion_factor)

    def add_corresponding_unit(self, unit1: str, unit2: str) -> None:
        """
        Add a correspondence between two units (e.g., power ↔ energy).

        Args:
            unit1: First unit (e.g., "MW")
            unit2: Corresponding unit (e.g., "MWh")

        Examples:
            >>> registry.add_corresponding_unit("hp", "hp·h")
            >>> registry.add_corresponding_unit("therm/h", "therm")
        """
        self._corresponding_units[unit1] = unit2
        self._corresponding_units[unit2] = unit1

    def add_dimension_conversion(
        self, from_dim: str, to_dim: str, conversion_func: Callable
    ) -> None:
        """
        Add a custom conversion function between dimensions.

        Args:
            from_dim: Source dimension
            to_dim: Target dimension
            conversion_func: Function that takes (value, substance, **kwargs) and returns converted value

        Examples:
            >>> def custom_energy_to_mass(value, substance, **kwargs):
            ...     # Custom conversion logic here
            ...     return value * custom_factor
            >>> registry.add_dimension_conversion("ENERGY", "MASS", custom_energy_to_mass)
        """
        # Store conversion function
        if not hasattr(self, "_custom_conversions"):
            self._custom_conversions = {}
        self._custom_conversions[(from_dim, to_dim)] = conversion_func

    def remove_unit(self, unit: str) -> None:
        """
        Remove a unit from the registry.

        Args:
            unit: Unit symbol to remove

        Raises:
            ValueError: If unit is a base unit or doesn't exist
        """
        if unit not in self._dimensions:
            raise ValueError(f"Unit '{unit}' not found in registry")

        dimension = self._dimensions[unit]
        if self._base_units.get(dimension) == unit:
            raise ValueError(
                f"Cannot remove base unit '{unit}' for dimension '{dimension}'"
            )

        # Remove from all registries
        del self._dimensions[unit]
        if unit in self._conversion_factors:
            del self._conversion_factors[unit]
        if unit in self._corresponding_units:
            corresponding = self._corresponding_units[unit]
            del self._corresponding_units[unit]
            if corresponding in self._corresponding_units:
                del self._corresponding_units[corresponding]

    def list_units(self, dimension: Optional[str] = None) -> Dict[str, str]:
        """
        List all units in the registry, optionally filtered by dimension.

        Args:
            dimension: Optional dimension filter

        Returns:
            Dictionary mapping unit → dimension
        """
        if dimension is None:
            return dict(self._dimensions)
        else:
            return {
                unit: dim for unit, dim in self._dimensions.items() if dim == dimension
            }

    def get_unit_info(self, unit: str) -> Dict[str, Any]:
        """
        Get detailed information about a unit.

        Args:
            unit: Unit symbol

        Returns:
            Dictionary with unit information

        Raises:
            ValueError: If unit not found
        """
        if unit not in self._dimensions:
            raise ValueError(f"Unit '{unit}' not found in registry")

        dimension = self._dimensions[unit]
        base_unit = self._base_units.get(dimension)
        conversion_factor = self._conversion_factors.get(unit, 1.0)
        corresponding = self._corresponding_units.get(unit)

        return {
            "unit": unit,
            "dimension": dimension,
            "base_unit": base_unit,
            "conversion_factor": conversion_factor,
            "corresponding_unit": corresponding,
            "is_base_unit": base_unit == unit,
        }

    def validate_registry(self) -> Dict[str, list]:
        """
        Validate the registry for consistency and return any issues found.

        Returns:
            Dictionary with lists of validation issues by category
        """
        issues = {
            "missing_conversion_factors": [],
            "orphaned_correspondences": [],
            "missing_base_units": [],
            "circular_correspondences": [],
        }

        # Check for missing conversion factors
        for unit, dimension in self._dimensions.items():
            base_unit = self._base_units.get(dimension)
            if unit != base_unit and unit not in self._conversion_factors:
                issues["missing_conversion_factors"].append(unit)

        # Check for orphaned correspondences
        for unit in self._corresponding_units:
            if unit not in self._dimensions:
                issues["orphaned_correspondences"].append(unit)

        # Check for missing base units
        for dimension, base_unit in self._base_units.items():
            if base_unit not in self._dimensions:
                issues["missing_base_units"].append((dimension, base_unit))

        # Check for circular correspondences (optional - may be desired)
        checked = set()
        for unit, corresponding in self._corresponding_units.items():
            if unit in checked:
                continue
            if corresponding in self._corresponding_units:
                if self._corresponding_units[corresponding] == unit:
                    checked.add(unit)
                    checked.add(corresponding)
                else:
                    issues["circular_correspondences"].append(unit)

        return issues


# Create a global registry instance
registry = UnitRegistry()
