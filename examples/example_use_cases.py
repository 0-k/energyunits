"""
EnergyUnits examples for energy system modeling.

Run with:  python examples/example_use_cases.py
"""

import warnings

import numpy as np

from energyunits import EnergyUnitsWarning, Quantity
from energyunits.units import GJ, MW, MWh, h


def basic_conversions():
    print("=== Unit conversions ===")
    energy = Quantity(100, "MWh")
    print(f"{energy} = {energy.to('GJ')} = {energy.to('MMBTU')} = {energy.to('toe')}")
    print(f"{Quantity(1, 'Mtoe')} = {Quantity(1, 'Mtoe').to('TWh')}")
    print(f"{Quantity(3600, 'GJ/h')} = {Quantity(3600, 'GJ/h').to('MW')}")
    print(f"{Quantity(40, 'EUR/kW/a')} = {Quantity(40, 'EUR/kW/a').to('EUR/MW/a')}")


def power_plant():
    print("\n=== Coal power plant ===")
    capacity = Quantity(500, "MW")
    full_load_hours = Quantity(6570, "h")
    generation = (capacity * full_load_hours).to("GWh")
    print(f"Generation:         {generation}")

    efficiency = 0.40
    fuel_energy = Quantity(generation.to("MWh").value / efficiency, "MWh", "coal")
    fuel_mass = fuel_energy.to("kt")
    co2 = fuel_energy.to("Mt", substance="CO2")
    print(f"Fuel input:         {fuel_energy.to('PJ')} = {fuel_mass}")
    print(f"CO2 emissions:      {co2}")

    intensity = (co2 / generation).to("t/MWh")
    print(f"Emission intensity: {intensity.value:.3f} t CO2/MWh(el)")

    capacity_factor = generation / (capacity * Quantity(8760, "h"))
    print(f"Capacity factor:    {float(capacity_factor):.1%}")


def gas_plant_emission_rate():
    print("\n=== Gas plant emission rate ===")
    fuel_input = Quantity(800, "MW", "natural_gas")  # thermal input (LHV)
    print(f"Fuel flow:  {fuel_input.to('t/h')}")
    print(f"CO2 rate:   {fuel_input.to('t/h', substance='CO2')}")
    print(f"Water rate: {fuel_input.to('t/h', substance='H2O')}")


def fuel_prices():
    print("\n=== Fuel prices ===")
    henry_hub = Quantity(3.5, "USD/MMBTU", "natural_gas", basis="HHV")
    print(f"Henry Hub {henry_hub} (HHV) = {henry_hub.to('USD/MWh', basis='LHV')} (LHV)")

    coal_price = Quantity(110, "USD/t", "bituminous")
    print(f"Coal {coal_price} = {coal_price.to('USD/MWh')} = {coal_price.to('USD/GJ')}")

    diesel = Quantity(1.6, "EUR/L", "diesel")
    print(f"Diesel {diesel} = {diesel.to('EUR/MWh')}")


def fuel_comparison():
    print("\n=== Fuel comparison per tonne ===")
    print(f"{'Fuel':<14}{'LHV (MWh)':>10}{'HHV (MWh)':>11}{'CO2 (t)':>9}{'kg CO2/MWh':>12}")
    for fuel in ["lignite", "bituminous", "natural_gas", "diesel", "hydrogen", "wood_pellets"]:
        tonne = Quantity(1, "t", fuel)
        lhv = tonne.to("MWh")
        hhv = tonne.to("MWh", basis="HHV")
        co2 = tonne.to("t", substance="CO2")
        intensity = (co2 / lhv).to("kg/MWh")
        print(f"{fuel:<14}{lhv.value:>10.2f}{hhv.value:>11.2f}{co2.value:>9.2f}{intensity.value:>12.0f}")
    print("(wood: biogenic CO2, usually reported as zero)")


def lcoe():
    print("\n=== Levelized cost of electricity (onshore wind) ===")
    capex = Quantity(1500, "USD/kW", reference_year=2020).to(reference_year=2024)
    fixed_om = Quantity(40, "USD/kW/a", reference_year=2024)
    capacity = Quantity(100, "MW")
    annual_generation = capacity * Quantity(3066, "h") / Quantity(1, "a")  # MWh/a
    lifetime, discount_rate = 25, 0.07

    crf = discount_rate * (1 + discount_rate) ** lifetime / ((1 + discount_rate) ** lifetime - 1)
    annualized_capex = capex * capacity * crf / Quantity(1, "a")  # USD/a
    annual_om = fixed_om * capacity  # USD/a

    lcoe_capex = (annualized_capex / annual_generation).to("USD/MWh")
    lcoe_om = (annual_om / annual_generation).to("USD/MWh")
    print(f"CAPEX (2024 USD):        {capex}")
    print(f"Annual generation:       {annual_generation.to('GWh/a')}")
    print(f"Capital recovery factor: {crf:.4f}")
    print(f"LCOE = {lcoe_capex} (capital) + {lcoe_om} (O&M) = {lcoe_capex + lcoe_om}")
    print(f"     = {(lcoe_capex + lcoe_om).to('EUR/MWh')} at the 2024 exchange rate")


def inflation_and_currencies():
    print("\n=== Inflation and exchange rates ===")
    for currency in ["USD", "EUR", "GBP", "JPY", "CNY"]:
        cost = Quantity(100, currency, reference_year=2015)
        print(f"100 {currency} (2015) = {cost.to(reference_year=2025)} (2025)")

    price = Quantity(50, "EUR/MWh", reference_year=2020)
    print(f"{price} (2020) = {price.to('USD/MWh')} at the 2020 rate")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", EnergyUnitsWarning)
        converted = Quantity(50, "EUR/MWh", reference_year=2015).to("USD/MWh", reference_year=2024)
    print(f"50 EUR/MWh (2015) = {converted} (2024; inflated in EUR, then converted)")

    total = Quantity(100, "USD", reference_year=2015) + Quantity(100, "USD", reference_year=2024)
    print(f"100 USD (2015) + 100 USD (2024) = {total} in {total.reference_year} prices")


def time_series():
    print("\n=== Time series ===")
    profile = np.array([0.2, 0.5, 0.9, 0.7, 0.3])
    capacity = Quantity(200, MW)
    hourly_power = profile * capacity
    hourly_energy = hourly_power * Quantity(1, h)
    print(f"Hourly power:  {hourly_power}")
    print(f"Energy:        {hourly_energy.sum()} = {hourly_energy.sum().to(GJ)}")
    print(f"Peak:          {hourly_power.max()}")

    prices = Quantity([40, 55, 90, 70, 45], "EUR/MWh")
    revenue = (hourly_energy * prices).sum()
    print(f"Revenue:       {revenue}")
    print(f"Average price: {(revenue / hourly_energy.sum()).to('EUR/MWh')}")


def storage():
    print("\n=== Battery storage ===")
    energy_capacity = Quantity(400, MWh)
    power_rating = Quantity(100, MW)
    print(f"Duration: {energy_capacity / power_rating}")
    print(f"Charging 90 min at full power: {power_rating * Quantity(90, 'min')}")


def discovery():
    print("\n=== Available data ===")
    print(f"Energy units: {', '.join(Quantity.list_units('ENERGY'))}")
    print(f"Fuels:        {', '.join(Quantity.list_substances('hhv'))}")
    print(f"Currencies:   {', '.join(Quantity.list_currencies())}")


if __name__ == "__main__":
    basic_conversions()
    power_plant()
    gas_plant_emission_rate()
    fuel_prices()
    fuel_comparison()
    lcoe()
    inflation_and_currencies()
    time_series()
    storage()
    discovery()
    print("\nDone.")
