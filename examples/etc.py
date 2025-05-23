from energyunits import Quantity

# Project parameters
capacity = Quantity(200, "MW")
capacity_factor = 0.35
capex = Quantity(1200, "USD/kW")


print()
# Calculate key metrics
annual_generation = capacity.for_duration(hours=8760) * capacity_factor
total_investment = capex * capacity.to("kW").value

print(annual_generation)
print(total_investment)
