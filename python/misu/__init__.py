"""misu — fast quantities (units of measurement) for Python."""
from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version as _pkg_version

try:
    __version__ = _pkg_version("misu")
except PackageNotFoundError:
    # Source tree without `maturin develop` having run yet.
    __version__ = "0.0.0+unknown"

from misu._engine import (
    EIncompatibleUnits,
    ESignatureAlreadyRegistered,
    Quantity,
    QuantityNP,
    addType,
    dimensions,
    quantity_from_string,
)

# Populate the package namespace with the unit catalogue.
from misu import _catalogue as _catalogue  # noqa: E402

_catalogue.populate()

# Re-export the helpers users may want from the misulib facade.
createUnit = _catalogue.createUnit
createMetricPrefixes = _catalogue.createMetricPrefixes

del _catalogue
