"""Unit constants for IDE-friendly autocompletion.

Instead of using raw strings, you can import unit constants for better
IDE support and typo prevention:

    from energyunits.units import MWh, GJ, MW, USD, EUR

    energy = Quantity(100, MWh)
    energy.to(GJ)

These are simple string constants — they work identically to passing
the string directly.
"""

# Energy units
J = "J"
kJ = "kJ"
MJ = "MJ"
GJ = "GJ"
TJ = "TJ"
PJ = "PJ"
EJ = "EJ"
Wh = "Wh"
kWh = "kWh"
MWh = "MWh"
GWh = "GWh"
TWh = "TWh"
PWh = "PWh"
MMBTU = "MMBTU"

# Power units
W = "W"
kW = "kW"
MW = "MW"
GW = "GW"
TW = "TW"

# Mass units
g = "g"
kg = "kg"
t = "t"
Mt = "Mt"
Gt = "Gt"

# Volume units
m3 = "m3"
L = "L"
barrel = "barrel"

# Time units
s = "s"
min = "min"
h = "h"
a = "a"

# Currency units
USD = "USD"
EUR = "EUR"
GBP = "GBP"
JPY = "JPY"
CNY = "CNY"
