"""
Substance module for the EnergyUnits library.

Contains database of substances with their properties for energy system modeling.
All values are stored in standard units:
- Heating values: MJ/kg
- Density: kg/m3
- Carbon intensity: kg CO2/MWh
- Content fractions: dimensionless (0-1)
"""


class SubstanceRegistry:
    """Registry of substances and their properties."""

    def __init__(self):
        """Initialize the substance registry."""
        self._substances = {
            # Coal
            "coal": {
                "name": "Coal (generic)",
                "hhv": 29.3,  # MJ/kg
                "lhv": 27.8,  # MJ/kg
                "density": 833,  # kg/m3
                "carbon_intensity": 340,  # kg CO2/MWh
                "carbon_content": 0.75,
                "hydrogen_content": 0.05,
                "ash_content": 0.10,
            },
            "lignite": {
                "name": "Lignite Coal",
                "hhv": 15.0,  # MJ/kg
                "lhv": 14.0,  # MJ/kg
                "density": 700,  # kg/m3
                "carbon_intensity": 400,  # kg CO2/MWh
                "carbon_content": 0.65,
                "hydrogen_content": 0.04,
                "ash_content": 0.15,
            },
            "bituminous": {
                "name": "Bituminous Coal",
                "hhv": 30.0,  # MJ/kg
                "lhv": 28.5,  # MJ/kg
                "density": 833,  # kg/m3
                "carbon_intensity": 330,  # kg CO2/MWh
                "carbon_content": 0.80,
                "hydrogen_content": 0.05,
                "ash_content": 0.08,
            },
            "anthracite": {
                "name": "Anthracite Coal",
                "hhv": 32.5,  # MJ/kg
                "lhv": 31.5,  # MJ/kg
                "density": 1000,  # kg/m3
                "carbon_intensity": 320,  # kg CO2/MWh
                "carbon_content": 0.85,
                "hydrogen_content": 0.04,
                "ash_content": 0.05,
            },
            # Natural Gas
            "natural_gas": {
                "name": "Natural Gas",
                "hhv": 55.0,  # MJ/kg
                "lhv": 49.5,  # MJ/kg
                "density": 0.75,  # kg/m3
                "carbon_intensity": 200,  # kg CO2/MWh
                "carbon_content": 0.75,
                "hydrogen_content": 0.25,
                "ash_content": 0.0,
            },
            "lng": {
                "name": "Liquefied Natural Gas",
                "hhv": 55.0,  # MJ/kg
                "lhv": 49.5,  # MJ/kg
                "density": 450,  # kg/m3
                "carbon_intensity": 210,  # kg CO2/MWh
                "carbon_content": 0.75,
                "hydrogen_content": 0.25,
                "ash_content": 0.0,
            },
            "methane": {
                "name": "Methane",
                "hhv": 55.5,  # MJ/kg
                "lhv": 50.0,  # MJ/kg
                "density": 0.68,  # kg/m3
                "carbon_intensity": 200,  # kg CO2/MWh
                "carbon_content": 0.75,
                "hydrogen_content": 0.25,
                "ash_content": 0.0,
            },
            # Oil Products
            "crude_oil": {
                "name": "Crude Oil",
                "hhv": 45.0,  # MJ/kg
                "lhv": 42.5,  # MJ/kg
                "density": 870,  # kg/m3
                "carbon_intensity": 270,  # kg CO2/MWh
                "carbon_content": 0.85,
                "hydrogen_content": 0.13,
                "ash_content": 0.001,
            },
            "oil": {
                "name": "Oil (generic)",
                "hhv": 45.0,  # MJ/kg
                "lhv": 42.5,  # MJ/kg
                "density": 870,  # kg/m3
                "carbon_intensity": 270,  # kg CO2/MWh
                "carbon_content": 0.85,
                "hydrogen_content": 0.13,
                "ash_content": 0.001,
            },
            "fuel_oil": {
                "name": "Heavy Fuel Oil",
                "hhv": 43.0,  # MJ/kg
                "lhv": 40.5,  # MJ/kg
                "density": 950,  # kg/m3
                "carbon_intensity": 285,  # kg CO2/MWh
                "carbon_content": 0.87,
                "hydrogen_content": 0.11,
                "ash_content": 0.005,
            },
            "diesel": {
                "name": "Diesel",
                "hhv": 45.7,  # MJ/kg
                "lhv": 42.8,  # MJ/kg
                "density": 840,  # kg/m3
                "carbon_intensity": 265,  # kg CO2/MWh
                "carbon_content": 0.86,
                "hydrogen_content": 0.14,
                "ash_content": 0.0,
            },
            "gasoline": {
                "name": "Gasoline",
                "hhv": 47.3,  # MJ/kg
                "lhv": 44.0,  # MJ/kg
                "density": 750,  # kg/m3
                "carbon_intensity": 255,  # kg CO2/MWh
                "carbon_content": 0.85,
                "hydrogen_content": 0.15,
                "ash_content": 0.0,
            },
            # Biomass
            "wood_pellets": {
                "name": "Wood Pellets",
                "hhv": 20.0,  # MJ/kg
                "lhv": 18.5,  # MJ/kg
                "density": 650,  # kg/m3
                "carbon_intensity": 20,  # kg CO2/MWh
                "carbon_content": 0.50,
                "hydrogen_content": 0.06,
                "ash_content": 0.01,
            },
            "wood_chips": {
                "name": "Wood Chips",
                "hhv": 19.0,  # MJ/kg
                "lhv": 16.0,  # MJ/kg
                "density": 350,  # kg/m3
                "carbon_intensity": 25,  # kg CO2/MWh
                "carbon_content": 0.48,
                "hydrogen_content": 0.06,
                "ash_content": 0.02,
            },
            # Renewables (no combustion)
            "wind": {
                "name": "Wind Energy",
                "hhv": None,
                "lhv": None,
                "density": None,
                "carbon_intensity": 0,  # kg CO2/MWh
                "carbon_content": 0.0,
                "hydrogen_content": 0.0,
                "ash_content": 0.0,
            },
            "solar": {
                "name": "Solar Energy",
                "hhv": None,
                "lhv": None,
                "density": None,
                "carbon_intensity": 0,  # kg CO2/MWh
                "carbon_content": 0.0,
                "hydrogen_content": 0.0,
                "ash_content": 0.0,
            },
            "hydro": {
                "name": "Hydro Energy",
                "hhv": None,
                "lhv": None,
                "density": None,
                "carbon_intensity": 0,  # kg CO2/MWh
                "carbon_content": 0.0,
                "hydrogen_content": 0.0,
                "ash_content": 0.0,
            },
            "nuclear": {
                "name": "Nuclear Energy",
                "hhv": None,
                "lhv": None,
                "density": None,
                "carbon_intensity": 0,  # kg CO2/MWh
                "carbon_content": 0.0,
                "hydrogen_content": 0.0,
                "ash_content": 0.0,
            },
            # Other fuels
            "hydrogen": {
                "name": "Hydrogen",
                "hhv": 142.0,  # MJ/kg
                "lhv": 120.0,  # MJ/kg
                "density": 0.09,  # kg/m3
                "carbon_intensity": 0,  # kg CO2/MWh
                "carbon_content": 0.0,
                "hydrogen_content": 1.0,
                "ash_content": 0.0,
            },
            "methanol": {
                "name": "Methanol",
                "hhv": 22.7,  # MJ/kg
                "lhv": 19.9,  # MJ/kg
                "density": 795,  # kg/m3
                "carbon_intensity": 240,  # kg CO2/MWh
                "carbon_content": 0.375,
                "hydrogen_content": 0.125,
                "ash_content": 0.0,
            },
            # Combustion products
            "CO2": {
                "name": "Carbon Dioxide",
                "hhv": None,
                "lhv": None,
                "density": 1.98,  # kg/m3
                "carbon_intensity": 0.0,
                "carbon_content": 0.273,
                "hydrogen_content": 0.0,
                "ash_content": 0.0,
            },
            "H2O": {
                "name": "Water",
                "hhv": None,
                "lhv": None,
                "density": 1000,  # kg/m3
                "carbon_intensity": 0.0,
                "carbon_content": 0.0,
                "hydrogen_content": 0.111,
                "ash_content": 0.0,
            },
            "ash": {
                "name": "Ash",
                "hhv": None,
                "lhv": None,
                "density": 1500,  # kg/m3
                "carbon_intensity": 0.0,
                "carbon_content": 0.0,
                "hydrogen_content": 0.0,
                "ash_content": 1.0,
            },
        }

        self._volumetric_units = {
            "barrel": 0.159,  # m3 per barrel
        }

    def __getitem__(self, substance_id):
        """Dict-like access to substance data."""
        if substance_id not in self._substances:
            raise ValueError(f"Unknown substance: {substance_id}")
        return self._substances[substance_id]

    def __contains__(self, substance_id):
        """Check if substance exists."""
        return substance_id in self._substances

    def hhv(self, substance_id):
        """Get higher heating value in MJ/kg."""
        substance = self[substance_id]
        hhv = substance["hhv"]
        if hhv is None:
            raise ValueError(
                f"Substance '{substance_id}' has no heating value (not a combustible fuel)"
            )
        return hhv

    def lhv(self, substance_id):
        """Get lower heating value in MJ/kg."""
        substance = self[substance_id]
        lhv = substance["lhv"]
        if lhv is None:
            raise ValueError(
                f"Substance '{substance_id}' has no heating value (not a combustible fuel)"
            )
        return lhv

    def density(self, substance_id):
        """Get density in kg/m3."""
        substance = self[substance_id]
        density = substance["density"]
        if density is None:
            raise ValueError(f"Substance '{substance_id}' has no defined density")
        return density

    def lhv_hhv_ratio(self, substance_id):
        """Get the ratio of LHV to HHV."""
        hhv = self.hhv(substance_id)
        lhv = self.lhv(substance_id)
        return lhv / hhv

    def calculate_combustion_product(self, fuel_quantity, target_substance):
        """Calculate combustion products from fuel based on stoichiometry."""
        from .quantity import Quantity

        if fuel_quantity.substance is None:
            raise ValueError(
                "Fuel substance must be specified for combustion product calculation"
            )

        # Convert to tonnes (base mass unit)
        fuel_t = fuel_quantity.to("t")
        fuel_mass = fuel_t.value

        substance = self[fuel_quantity.substance]

        if target_substance == "CO2":
            carbon_fraction = substance["carbon_content"]
            carbon_mass = fuel_mass * carbon_fraction
            co2_mass = carbon_mass * (44 / 12)  # C + O2 → CO2
            return Quantity(co2_mass, "t", "CO2")

        elif target_substance == "H2O":
            hydrogen_fraction = substance["hydrogen_content"]
            hydrogen_mass = fuel_mass * hydrogen_fraction
            water_mass = hydrogen_mass * (18 / 2)  # 2H + ½O2 → H2O
            return Quantity(water_mass, "t", "H2O")

        elif target_substance == "ash":
            ash_fraction = substance["ash_content"]
            ash_mass = fuel_mass * ash_fraction
            return Quantity(ash_mass, "t", "ash")

        else:
            raise ValueError(f"Unknown combustion product: {target_substance}")

    def add_substance(self, name: str, properties: dict) -> None:
        """
        Add a new substance to the registry at runtime.

        Args:
            name: Substance identifier (e.g., "my_coal", "custom_gas")
            properties: Dictionary of substance properties

        Required properties:
            - hhv: Higher heating value (MJ/kg)
            - lhv: Lower heating value (MJ/kg)
            - density: Density (kg/m3)
            - carbon_intensity: Carbon intensity (kg CO2/MWh)
            - carbon_content: Carbon content fraction (0-1)

        Optional properties:
            - name: Display name (defaults to name parameter)
            - hydrogen_content: Hydrogen content fraction (0-1)
            - ash_content: Ash content fraction (0-1)
            - description: Text description

        Examples:
            >>> substance_registry.add_substance("my_coal", {
            ...     "name": "My Custom Coal",
            ...     "hhv": 30.0,
            ...     "lhv": 28.5,
            ...     "density": 800,
            ...     "carbon_intensity": 350,
            ...     "carbon_content": 0.80,
            ...     "ash_content": 0.08
            ... })
        """
        required_props = ["hhv", "lhv", "density", "carbon_intensity", "carbon_content"]

        # Validate required properties
        for prop in required_props:
            if prop not in properties:
                raise ValueError(
                    f"Missing required property '{prop}' for substance '{name}'"
                )

        # Set default name if not provided
        if "name" not in properties:
            properties["name"] = name

        # Set defaults for optional properties
        properties.setdefault("hydrogen_content", 0.0)
        properties.setdefault("ash_content", 0.0)
        properties.setdefault("description", f"User-defined substance: {name}")

        # Add to registry
        self._substances[name] = properties.copy()

    def update_substance(self, name: str, properties: dict) -> None:
        """
        Update properties of an existing substance.

        Args:
            name: Substance identifier
            properties: Dictionary of properties to update

        Raises:
            ValueError: If substance doesn't exist
        """
        if name not in self._substances:
            raise ValueError(f"Substance '{name}' not found in registry")

        # Update existing substance
        self._substances[name].update(properties)

    def remove_substance(self, name: str) -> None:
        """
        Remove a substance from the registry.

        Args:
            name: Substance identifier to remove

        Raises:
            ValueError: If substance doesn't exist
        """
        if name not in self._substances:
            raise ValueError(f"Substance '{name}' not found in registry")

        del self._substances[name]

    def list_substances(self) -> list:
        """
        List all substances in the registry.

        Returns:
            List of substance identifiers
        """
        return list(self._substances.keys())

    def get_substance_info(self, name: str) -> dict:
        """
        Get complete information about a substance.

        Args:
            name: Substance identifier

        Returns:
            Dictionary with all substance properties

        Raises:
            ValueError: If substance doesn't exist
        """
        if name not in self._substances:
            raise ValueError(f"Substance '{name}' not found in registry")

        return self._substances[name].copy()

    def search_substances(self, **criteria) -> list:
        """
        Search for substances matching given criteria.

        Args:
            **criteria: Property criteria to match
                       (e.g., carbon_content__gt=0.7, hhv__range=(25, 35))

        Returns:
            List of substance names matching criteria

        Examples:
            >>> # Find high-carbon substances
            >>> high_carbon = substance_registry.search_substances(carbon_content__gt=0.7)
            >>>
            >>> # Find substances with HHV in range
            >>> mid_hhv = substance_registry.search_substances(hhv__range=(20, 40))
        """
        matches = []

        for name, substance in self._substances.items():
            match = True

            for criterion, value in criteria.items():
                if "__" in criterion:
                    prop, operator = criterion.split("__", 1)
                else:
                    prop, operator = criterion, "eq"

                if prop not in substance:
                    match = False
                    break

                substance_value = substance[prop]

                # Skip None values for comparison operators
                if substance_value is None and operator in [
                    "gt",
                    "lt",
                    "gte",
                    "lte",
                    "range",
                ]:
                    match = False
                    break

                if operator == "eq":
                    if substance_value != value:
                        match = False
                        break
                elif operator == "gt":
                    if substance_value <= value:
                        match = False
                        break
                elif operator == "lt":
                    if substance_value >= value:
                        match = False
                        break
                elif operator == "gte":
                    if substance_value < value:
                        match = False
                        break
                elif operator == "lte":
                    if substance_value > value:
                        match = False
                        break
                elif operator == "range":
                    if not (value[0] <= substance_value <= value[1]):
                        match = False
                        break
                elif operator == "in":
                    if substance_value not in value:
                        match = False
                        break
                else:
                    raise ValueError(f"Unknown operator: {operator}")

            if match:
                matches.append(name)

        return matches

    def validate_substance(self, name: str) -> dict:
        """
        Validate a substance's properties for consistency.

        Args:
            name: Substance identifier

        Returns:
            Dictionary with validation results and any issues found

        Raises:
            ValueError: If substance doesn't exist
        """
        if name not in self._substances:
            raise ValueError(f"Substance '{name}' not found in registry")

        substance = self._substances[name]
        issues = []
        warnings = []

        # Check LHV vs HHV relationship
        if substance["lhv"] > substance["hhv"]:
            issues.append("LHV cannot be greater than HHV")

        # Check content fractions
        total_content = (
            substance.get("carbon_content", 0)
            + substance.get("hydrogen_content", 0)
            + substance.get("ash_content", 0)
        )

        if total_content > 1.0:
            issues.append(f"Total content fractions exceed 1.0 ({total_content:.3f})")
        elif total_content < 0.8:
            warnings.append(
                f"Total content fractions unusually low ({total_content:.3f})"
            )

        # Check reasonable value ranges
        if substance["density"] <= 0:
            issues.append("Density must be positive")
        if substance["hhv"] <= 0:
            issues.append("HHV must be positive")
        if substance["carbon_intensity"] < 0:
            issues.append("Carbon intensity cannot be negative")

        return {"valid": len(issues) == 0, "issues": issues, "warnings": warnings}


# Global instance
substance_registry = SubstanceRegistry()
