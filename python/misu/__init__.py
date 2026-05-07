"""misu — fast quantities (units of measurement) for Python."""
from __future__ import annotations

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
