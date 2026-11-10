"""
Pandas integration for the EnergyUnits library.

Unit metadata is stored in :attr:`pandas.DataFrame.attrs` under the keys
``"<column>_unit"`` and, optionally, ``"<column>_substance"``,
``"<column>_basis"`` and ``"<column>_reference_year"``. Conversions go through
:meth:`energyunits.Quantity.to`, so they support everything a ``Quantity``
supports (compound units, substances, exchange rates, inflation).

Example::

    import pandas as pd
    from energyunits.pandas_tools import add_units, convert_units, to_quantity

    df = pd.DataFrame({"generation": [100, 200, 300]})
    df = add_units(df, "generation", "MWh")
    df_gj = convert_units(df, "generation", "GJ")
    total = to_quantity(df_gj, "generation").sum()   # Quantity in GJ

Note:
    pandas does not propagate ``attrs`` through every operation (for example
    ``groupby`` or ``merge``). Re-attach units with :func:`add_units` after such
    operations.
"""

from typing import Optional

from .quantity import Quantity

_FIELDS = ("unit", "substance", "basis", "reference_year")


def _key(column, field: str) -> str:
    return f"{column}_{field}"


def add_units(df, column, unit: str, substance: Optional[str] = None, basis=None, reference_year=None):
    """Return a copy of ``df`` with unit metadata attached to ``column``.

    Args:
        df: pandas DataFrame.
        column: Column name to add units to.
        unit: Unit string (validated).
        substance: Optional substance of the column values (e.g. ``"coal"``).
        basis: Optional heating value basis (``"HHV"``/``"LHV"``).
        reference_year: Optional price base year for monetary columns.

    Returns:
        DataFrame copy with unit information in ``attrs``.
    """
    template = Quantity(0.0, unit, substance=substance, basis=basis, reference_year=reference_year)
    df_copy = df.copy()
    for field in _FIELDS:
        value = getattr(template, field)
        if value is None:
            df_copy.attrs.pop(_key(column, field), None)
        else:
            df_copy.attrs[_key(column, field)] = value
    return df_copy


def get_units(df, column) -> Optional[str]:
    """Unit attached to ``column``, or ``None`` if there is none."""
    return df.attrs.get(_key(column, "unit"))


def to_quantity(df, column) -> Quantity:
    """Column values and metadata as a :class:`~energyunits.Quantity`.

    Raises:
        ValueError: if the column has no unit information.
    """
    unit = get_units(df, column)
    if unit is None:
        raise ValueError(f"No unit information found for column '{column}'")
    return Quantity(
        df[column],
        unit,
        substance=df.attrs.get(_key(column, "substance")),
        basis=df.attrs.get(_key(column, "basis")),
        reference_year=df.attrs.get(_key(column, "reference_year")),
    )


def from_quantity(df, column, quantity: Quantity):
    """Return a copy of ``df`` with ``column`` set to the values and metadata of ``quantity``."""
    df_copy = add_units(
        df,
        column,
        quantity.unit,
        substance=quantity.substance,
        basis=quantity.basis,
        reference_year=quantity.reference_year,
    )
    df_copy[column] = quantity.value
    return df_copy


def convert_units(df, column, target_unit: Optional[str] = None, basis=None, reference_year=None):
    """Convert a column to another unit, heating value basis and/or reference year.

    Args:
        df: pandas DataFrame with unit information for ``column``.
        column: Column name to convert.
        target_unit: Target unit.
        basis: Optional target heating value basis.
        reference_year: Optional target price base year (inflation adjustment).

    Returns:
        DataFrame copy with converted values and updated unit information.

    Raises:
        ValueError: if the column has no unit information or the conversion is impossible.
    """
    converted = to_quantity(df, column).to(target_unit, basis=basis, reference_year=reference_year)
    return from_quantity(df, column, converted)
