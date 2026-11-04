"""Unit constants for IDE-friendly autocompletion.

Instead of raw strings you can import unit constants for better IDE support
and typo prevention::

    from energyunits.units import MWh, GJ, MW, USD, EUR

    energy = Quantity(100, MWh)
    energy.to(GJ)

The constants are plain strings and work identically to passing the string.
Compound units are built with ordinary string formatting, e.g. ``f"{EUR}/{MWh}"``.

Note: ``min`` (minute) is not exported by ``from energyunits.units import *``
to avoid shadowing the built-in ``min()``; import it explicitly if needed.
"""

# Energy
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
BTU = "BTU"  # International Table BTU
kBTU = "kBTU"  # thousand BTU
MMBTU = "MMBTU"  # million BTU
therm = "therm"  # 100,000 BTU
quad = "quad"  # 10^15 BTU
kcal = "kcal"  # International Table calorie
Mcal = "Mcal"
Gcal = "Gcal"
toe = "toe"  # tonne of oil equivalent (41.868 GJ)
ktoe = "ktoe"
Mtoe = "Mtoe"
tce = "tce"  # tonne of coal equivalent (29.3076 GJ)
Mtce = "Mtce"

# Power
W = "W"
kW = "kW"
MW = "MW"
GW = "GW"
TW = "TW"

# Mass
g = "g"
kg = "kg"
t = "t"
kt = "kt"
Mt = "Mt"
Gt = "Gt"
lb = "lb"  # avoirdupois pound

# Volume
L = "L"
m3 = "m3"
Sm3 = "Sm3"  # standard cubic metre of gas (15 °C, 101.325 kPa)
Nm3 = "Nm3"  # normal cubic metre of gas (0 °C, 101.325 kPa)
bcm = "bcm"  # billion cubic metres
barrel = "barrel"  # US oil barrel (42 US gal)
gal = "gal"  # US gallon
ft3 = "ft3"  # cubic foot
Mcf = "Mcf"  # thousand cubic feet
Bcf = "Bcf"  # billion cubic feet

# Area
m2 = "m2"
km2 = "km2"
ha = "ha"  # hectare
acre = "acre"  # international acre
ft2 = "ft2"  # square foot

# Time
s = "s"
min = "min"
h = "h"
d = "d"  # day
a = "a"  # year of 8760 h
yr = "yr"  # year of 8760 h (alias of a)

# Currency
USD = "USD"
kUSD = "kUSD"
MUSD = "MUSD"
bnUSD = "bnUSD"
EUR = "EUR"
kEUR = "kEUR"
MEUR = "MEUR"
bnEUR = "bnEUR"
GBP = "GBP"
kGBP = "kGBP"
MGBP = "MGBP"
bnGBP = "bnGBP"
JPY = "JPY"
kJPY = "kJPY"
MJPY = "MJPY"
bnJPY = "bnJPY"
CNY = "CNY"
kCNY = "kCNY"
MCNY = "MCNY"
bnCNY = "bnCNY"

__all__ = [
    "J",
    "kJ",
    "MJ",
    "GJ",
    "TJ",
    "PJ",
    "EJ",
    "Wh",
    "kWh",
    "MWh",
    "GWh",
    "TWh",
    "PWh",
    "BTU",
    "kBTU",
    "MMBTU",
    "therm",
    "quad",
    "kcal",
    "Mcal",
    "Gcal",
    "toe",
    "ktoe",
    "Mtoe",
    "tce",
    "Mtce",
    "W",
    "kW",
    "MW",
    "GW",
    "TW",
    "g",
    "kg",
    "t",
    "kt",
    "Mt",
    "Gt",
    "lb",
    "L",
    "m3",
    "Sm3",
    "Nm3",
    "bcm",
    "barrel",
    "gal",
    "ft3",
    "Mcf",
    "Bcf",
    "m2",
    "km2",
    "ha",
    "acre",
    "ft2",
    "s",
    "h",
    "d",
    "a",
    "yr",
    "USD",
    "kUSD",
    "MUSD",
    "bnUSD",
    "EUR",
    "kEUR",
    "MEUR",
    "bnEUR",
    "GBP",
    "kGBP",
    "MGBP",
    "bnGBP",
    "JPY",
    "kJPY",
    "MJPY",
    "bnJPY",
    "CNY",
    "kCNY",
    "MCNY",
    "bnCNY",
]
