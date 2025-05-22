"""
Substance module for the EnergyUnits library.

This module contains a database of substances with their properties
(heating values, densities, carbon intensities) and related functions.

Example:
    ```python
    from energyunits import Quantity

    # Get energy content of coal
    coal = Quantity(1000, "t", "coal")
    energy_hhv = coal.energy_content(basis="HHV")  # ~8140 MWh

    # Calculate CO2 emissions
    emissions = energy_hhv.calculate_emissions()  # tCO2
    ```
"""

import numpy as np


class SubstanceRegistry:
    """Registry of substances and their properties."""

    def __init__(self):
        """Initialize the substance registry with default values."""
        # Database format:
        # 'substance_id': {
        #     'name': 'Human readable name',
        #     'hhv': value in MJ/kg,
        #     'lhv': value in MJ/kg,
        #     'density': value in kg/m3,
        #     'carbon_intensity': value in kg CO2/MWh (LHV basis),
        #     'moisture_content': typical moisture content (mass fraction),
        # }
        self._substances = {
            # Coal
            "coal": {
                "name": "Coal (generic)",
                "hhv": 29.3,  # MJ/kg
                "lhv": 27.8,  # MJ/kg
                "density": 833,  # kg/m3 (bulk density)
                "carbon_intensity": 340,  # kg CO2/MWh
                "moisture_content": 0.10,  # 10% moisture typical
            },
            "lignite": {
                "name": "Lignite Coal",
                "hhv": 15.0,  # MJ/kg
                "lhv": 14.0,  # MJ/kg
                "density": 700,  # kg/m3
                "carbon_intensity": 400,  # kg CO2/MWh
                "moisture_content": 0.40,  # 40% moisture typical
            },
            "bituminous": {
                "name": "Bituminous Coal",
                "hhv": 30.0,  # MJ/kg
                "lhv": 28.5,  # MJ/kg
                "density": 833,  # kg/m3
                "carbon_intensity": 330,  # kg CO2/MWh
                "moisture_content": 0.05,  # 5% moisture typical
            },
            "anthracite": {
                "name": "Anthracite Coal",
                "hhv": 32.5,  # MJ/kg
                "lhv": 31.5,  # MJ/kg
                "density": 1000,  # kg/m3
                "carbon_intensity": 320,  # kg CO2/MWh
                "moisture_content": 0.03,  # 3% moisture typical
            },
            # Natural Gas
            "natural_gas": {
                "name": "Natural Gas",
                "hhv": 55.0,  # MJ/kg
                "lhv": 49.5,  # MJ/kg
                "density": 0.75,  # kg/m3
                "carbon_intensity": 200,  # kg CO2/MWh
                "moisture_content": 0.0,  # 0% moisture
            },
            "lng": {
                "name": "Liquefied Natural Gas",
                "hhv": 55.0,  # MJ/kg
                "lhv": 49.5,  # MJ/kg
                "density": 450,  # kg/m3
                "carbon_intensity": 210,  # kg CO2/MWh (slightly higher due to liquefaction process)
                "moisture_content": 0.0,  # 0% moisture
            },
            # Oil Products
            "crude_oil": {
                "name": "Crude Oil",
                "hhv": 45.0,  # MJ/kg
                "lhv": 42.5,  # MJ/kg
                "density": 870,  # kg/m3
                "carbon_intensity": 270,  # kg CO2/MWh
                "moisture_content": 0.0,  # 0% moisture
            },
            "oil": {  # Generic oil for tests
                "name": "Oil (generic)",
                "hhv": 45.0,  # MJ/kg
                "lhv": 42.5,  # MJ/kg
                "density": 870,  # kg/m3
                "carbon_intensity": 270,  # kg CO2/MWh
                "moisture_content": 0.0,  # 0% moisture
            },
            "fuel_oil": {
                "name": "Heavy Fuel Oil",
                "hhv": 43.0,  # MJ/kg
                "lhv": 40.5,  # MJ/kg
                "density": 950,  # kg/m3
                "carbon_intensity": 285,  # kg CO2/MWh
                "moisture_content": 0.0,  # 0% moisture
            },
            "diesel": {
                "name": "Diesel",
                "hhv": 45.7,  # MJ/kg
                "lhv": 42.8,  # MJ/kg
                "density": 840,  # kg/m3
                "carbon_intensity": 265,  # kg CO2/MWh
                "moisture_content": 0.0,  # 0% moisture
            },
            "gasoline": {
                "name": "Gasoline",
                "hhv": 47.3,  # MJ/kg
                "lhv": 44.0,  # MJ/kg
                "density": 750,  # kg/m3
                "carbon_intensity": 255,  # kg CO2/MWh
                "moisture_content": 0.0,  # 0% moisture
            },
            # Biomass
            "wood_pellets": {
                "name": "Wood Pellets",
                "hhv": 20.0,  # MJ/kg
                "lhv": 18.5,  # MJ/kg
                "density": 650,  # kg/m3
                "carbon_intensity": 20,  # kg CO2/MWh (considered renewable)
                "moisture_content": 0.08,  # 8% moisture typical for pellets
            },
            "wood_chips": {
                "name": "Wood Chips",
                "hhv": 19.0,  # MJ/kg
                "lhv": 16.0,  # MJ/kg
                "density": 350,  # kg/m3
                "carbon_intensity": 25,  # kg CO2/MWh (considered renewable)
                "moisture_content": 0.30,  # 30% moisture typical
            },
            # Other fuels
            "hydrogen": {
                "name": "Hydrogen",
                "hhv": 142.0,  # MJ/kg
                "lhv": 120.0,  # MJ/kg
                "density": 0.09,  # kg/m3 (at standard conditions)
                "carbon_intensity": 0,  # kg CO2/MWh (zero direct emissions)
                "moisture_content": 0.0,  # 0% moisture
            },
            "methanol": {
                "name": "Methanol",
                "hhv": 22.7,  # MJ/kg
                "lhv": 19.9,  # MJ/kg
                "density": 795,  # kg/m3
                "carbon_intensity": 240,  # kg CO2/MWh
                "moisture_content": 0.0,  # 0% moisture
            },
            # Greenhouse gases
            "CO2": {
                "name": "Carbon Dioxide",
                "hhv": 0.0,  # MJ/kg (not a fuel)
                "lhv": 0.0,  # MJ/kg
                "density": 1.98,  # kg/m3 (at standard conditions)
                "carbon_intensity": 0.0,  # kg CO2/MWh (not applicable)
                "moisture_content": 0.0,  # 0% moisture
            },
            "methane": {
                "name": "Methane",
                "hhv": 55.5,  # MJ/kg
                "lhv": 50.0,  # MJ/kg
                "density": 0.68,  # kg/m3 (at standard conditions)
                "carbon_intensity": 200,  # kg CO2/MWh
                "moisture_content": 0.0,  # 0% moisture
            },
        }

        # Unit conversions
        self._volumetric_units = {
            "barrel": 0.159,  # m3 per barrel
        }

    def get_substance(self, substance_id):
        """Get substance data by ID."""
        if substance_id not in self._substances:
            raise ValueError(f"Unknown substance: {substance_id}")

        return self._substances[substance_id]

    def get_hhv(self, substance_id, unit="MJ/kg"):
        """Get higher heating value (HHV) for a substance."""
        substance = self.get_substance(substance_id)
        hhv = substance["hhv"]

        # Convert from MJ/kg to requested unit
        if unit == "MJ/kg":
            return hhv
        elif unit == "MWh/t":
            return hhv * 0.2778  # 1 MJ/kg = 0.2778 MWh/t
        elif unit == "kWh/kg":
            return hhv * 0.2778  # 1 MJ/kg = 0.2778 kWh/kg
        else:
            raise ValueError(f"Unsupported HHV unit: {unit}")

    def get_lhv(self, substance_id, unit="MJ/kg"):
        """Get lower heating value (LHV) for a substance."""
        substance = self.get_substance(substance_id)
        lhv = substance["lhv"]

        # Convert from MJ/kg to requested unit
        if unit == "MJ/kg":
            return lhv
        elif unit == "MWh/t":
            return lhv * 0.2778  # 1 MJ/kg = 0.2778 MWh/t
        elif unit == "kWh/kg":
            return lhv * 0.2778  # 1 MJ/kg = 0.2778 kWh/kg
        else:
            raise ValueError(f"Unsupported LHV unit: {unit}")

    def get_density(self, substance_id):
        """Get density for a substance in kg/m3."""
        substance = self.get_substance(substance_id)
        return substance["density"]

    def get_carbon_intensity(self, substance_id):
        """Get carbon intensity for a substance in kg CO2/MWh."""
        substance = self.get_substance(substance_id)
        return substance["carbon_intensity"]

    def get_moisture_content(self, substance_id):
        """Get typical moisture content for a substance."""
        substance = self.get_substance(substance_id)
        return substance["moisture_content"]

    def get_lhv_hhv_ratio(self, substance_id):
        """Get the ratio of LHV to HHV for a substance."""
        substance = self.get_substance(substance_id)
        return substance["lhv"] / substance["hhv"]

    def calculate_energy_content(self, quantity, basis="HHV"):
        """Calculate energy content for a substance quantity.

        Args:
            quantity: A Quantity object with substance attribute
            basis: 'HHV' or 'LHV'

        Returns:
            A Quantity object with energy in MWh
        """
        from .quantity import Quantity

        if quantity.substance is None:
            raise ValueError(
                "Substance must be specified for energy content calculation"
            )

        substance_id = quantity.substance

        # Convert to mass units if not already
        if quantity.unit in ["t", "kg", "g"]:
            # Already in mass units, convert to tonnes
            mass_t = quantity.to("t").value
        elif quantity.unit in ["m3", "L"] + list(self._volumetric_units.keys()):
            # Convert from volume to mass
            if quantity.unit in self._volumetric_units:
                # Convert to m3 first
                volume_m3 = quantity.value * self._volumetric_units[quantity.unit]
            elif quantity.unit == "L":
                volume_m3 = quantity.value * 0.001
            else:  # m3
                volume_m3 = quantity.value

            # Convert to tonnes
            density = self.get_density(substance_id)  # kg/m3
            mass_t = (volume_m3 * density) / 1000  # t
        else:
            raise ValueError(
                f"Cannot calculate energy content from unit: {quantity.unit}"
            )

        # Get heating value in MWh/t
        if basis.upper() == "HHV":
            heating_value = self.get_hhv(substance_id, "MWh/t")
        elif basis.upper() == "LHV":
            heating_value = self.get_lhv(substance_id, "MWh/t")
        else:
            raise ValueError(f"Invalid heating value basis: {basis}")

        # Calculate energy content
        energy_mwh = mass_t * heating_value

        # Return as a new quantity
        return Quantity(energy_mwh, "MWh", substance_id)

    def calculate_emissions(self, energy_quantity):
        """Calculate CO2 emissions for an energy quantity.

        Args:
            energy_quantity: A Quantity object with energy units and substance

        Returns:
            A Quantity object with CO2 emissions in t
        """
        from .quantity import Quantity

        if energy_quantity.substance is None:
            raise ValueError("Substance must be specified for emissions calculation")

        if energy_quantity.dimension != "ENERGY":
            raise ValueError(f"Expected energy units, got: {energy_quantity.unit}")

        # Convert to MWh
        energy_mwh = energy_quantity.to("MWh").value

        # Get carbon intensity in kg CO2/MWh
        intensity = self.get_carbon_intensity(energy_quantity.substance)

        # Calculate emissions
        emissions_kg = energy_mwh * intensity
        emissions_t = emissions_kg / 1000

        # Return as a new quantity
        return Quantity(emissions_t, "t", "CO2")


# Create a global substance registry instance
substance_registry = SubstanceRegistry()
