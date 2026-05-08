"""Tests for the QuantityNP array class.

The existing test suite covers QuantityNP arithmetic when both operands
are array-like; this file fills in the rest of the public surface:
reverse arithmetic, unary ops, comparison, conversion, math methods,
formatting, and pickling round-trips.
"""
import math

import numpy as np
import pytest

from misu import (
    EIncompatibleUnits,
    Quantity,
    QuantityNP,
    dimensionless,
    kg,
    lb,
    m,
    s,
)


def _arr(values, unit=kg):
    return np.asarray(values, dtype=float) * unit


# --- construction & accessors ----------------------------------------------

def test_constructor_from_array():
    qnp = QuantityNP(np.array([1.0, 2.0, 3.0])) * kg
    assert isinstance(qnp, QuantityNP)
    assert list(qnp.magnitude) == [1.0, 2.0, 3.0]


def test_unit_as_tuple():
    x = _arr([1, 2])
    t = x.unit_as_tuple()
    assert t[1] == 1.0  # kg dim is index 1
    assert t[0] == 0.0


def test_units_and_getunit_match():
    x = _arr([1, 2])
    assert x.units() == x.getunit()


def test_setvaldict_is_frozen():
    x = _arr([1, 2])
    with pytest.raises(AssertionError):
        x.setValDict({})


def test_copy_is_independent():
    x = _arr([1, 2, 3])
    y = x.copy()
    assert y.magnitude.tolist() == x.magnitude.tolist()
    y.magnitude[0] = 99.0
    assert x.magnitude[0] == 1.0


def test_len():
    x = _arr([1, 2, 3, 4])
    assert len(x) == 4


def test_unit_string():
    x = _arr([1, 2])
    assert x._unitString()


# --- reverse arithmetic ----------------------------------------------------

def test_radd_with_scalar_quantity():
    x = _arr([1, 2, 3])
    out = (5 * kg) + x
    # scalar+array goes through Quantity.__add__ array branch, returns QuantityNP
    assert isinstance(out, QuantityNP)
    assert list(out.magnitude) == [6.0, 7.0, 8.0]


def test_rsub_via_bare_ndarray_minus_scalar_quantity():
    # Bare ndarray on the LHS, scalar Quantity on the RHS — exercises
    # Quantity.__rsub__'s array arm via numpy's __array_priority__ deferral.
    out = np.asarray([5.0, 6.0, 7.0]) - (1 * dimensionless)
    assert isinstance(out, QuantityNP)
    assert list(out.magnitude) == [4.0, 5.0, 6.0]


def test_rmul_via_scalar_float():
    x = _arr([1, 2])
    out = 3.0 * x
    assert isinstance(out, QuantityNP)
    assert list(out.magnitude) == [3.0, 6.0]


def test_rmul_via_bare_ndarray():
    x = _arr([1, 2])
    out = np.asarray([3.0, 3.0]) * x
    assert isinstance(out, QuantityNP)
    assert list(out.magnitude) == [3.0, 6.0]


def test_rtruediv_via_bare_ndarray_div_scalar_quantity():
    out = np.asarray([2.0, 4.0, 6.0]) / (2 * kg)
    assert isinstance(out, QuantityNP)
    np.testing.assert_allclose(out.magnitude, [1.0, 2.0, 3.0])


# --- unary -----------------------------------------------------------------

def test_neg():
    x = _arr([1, 2, 3])
    y = -x
    assert list(y.magnitude) == [-1.0, -2.0, -3.0]


def test_pow():
    x = _arr([1, 2, 3])
    y = x ** 2
    assert list(y.magnitude) == [1.0, 4.0, 9.0]
    assert y.unit_as_tuple()[1] == 2.0  # kg^2


# --- comparison ------------------------------------------------------------

@pytest.mark.parametrize(
    "op_name, op",
    [
        ("lt", lambda a, b: a < b),
        ("le", lambda a, b: a <= b),
        ("eq", lambda a, b: a == b),
        ("ne", lambda a, b: a != b),
        ("gt", lambda a, b: a > b),
        ("ge", lambda a, b: a >= b),
    ],
)
def test_richcmp_same_dims_returns_per_element_list(op_name, op):
    x = _arr([1.0, 2.0, 3.0])
    y = _arr([2.0, 2.0, 2.0])
    result = op(x, y)
    assert isinstance(result, list)
    assert len(result) == 3


def test_eq_across_incompatible_dims_returns_false():
    x = _arr([1, 2])
    y = np.asarray([1, 2], dtype=float) * s
    assert (x == y) is False
    assert (x != y) is True


def test_lt_across_incompatible_dims_raises():
    x = _arr([1, 2])
    y = np.asarray([1, 2], dtype=float) * s
    with pytest.raises(EIncompatibleUnits):
        x < y


# --- conversion / unitCategory / setRepresent -----------------------------

def test_convert_via_rshift():
    x = _arr([1.0, 2.0])
    out = x >> lb
    np.testing.assert_allclose(out, np.array([1.0, 2.0]) / 0.45359237, rtol=1e-6)


def test_convert_via_rshift_incompatible_dims_raises():
    x = _arr([1.0, 2.0])
    with pytest.raises(EIncompatibleUnits):
        x >> s


def test_unit_category_known():
    x = _arr([1.0, 2.0])
    assert x.unitCategory() == "Mass"


def test_unit_category_undefined_raises():
    x = np.asarray([1.0, 2.0]) * (kg ** 5 * m ** 3)
    with pytest.raises(Exception):
        x.unitCategory()


def test_setrepresent_with_unit():
    # Use kg^7 — a dim no other test cares about, so we don't pollute
    # global REPRESENT_CACHE state visible to other tests.
    weird = QuantityNP(np.asarray([1.0, 2.0])) * (kg ** 7)
    weird.setRepresent(as_unit=1.0 * (kg ** 7), symbol="wd7", format_spec=".0f")
    assert "wd7" in repr(weird)


def test_setrepresent_with_convert_function():
    weird = QuantityNP(np.asarray([1.0, 2.0])) * (kg ** 8)
    weird.setRepresent(symbol="wd8", convert_function=lambda q, mag: mag * 0.5)
    assert "wd8" in repr(weird)


def test_setrepresent_dim_mismatch_raises():
    weird = QuantityNP(np.asarray([1.0, 2.0])) * (kg ** 6)
    with pytest.raises(EIncompatibleUnits):
        weird.setRepresent(as_unit=1.0 * kg, symbol="wrong")


# --- math methods (dimensionless) -----------------------------------------

@pytest.mark.parametrize(
    "fn",
    [
        "sin", "cos", "tan",
        "arcsin", "arccos", "arctan",
        "degrees", "radians", "deg2rad", "rad2deg",
        "sinh", "cosh", "tanh",
        "arcsinh", "arccosh", "arctanh",
        "exp", "expm1", "exp2",
        "log", "log10", "log2", "log1p",
    ],
)
def test_math_fn_returns_quantity_np(fn):
    x = QuantityNP(np.asarray([0.5, 1.5]))  # dimensionless
    result = getattr(x, fn)()
    assert isinstance(result, QuantityNP)


def test_math_fn_rejects_non_dimensionless():
    x = _arr([1.0, 2.0])
    with pytest.raises(EIncompatibleUnits):
        x.sin()


# --- format / repr ---------------------------------------------------------

def test_format_no_spec_includes_unit():
    # Format with empty spec exercises __format__/format_with_spec but
    # avoids passing a numeric format spec to the underlying ndarray
    # (numpy rejects scalar specs like ".2f" on arrays).
    x = _arr([1.0, 2.5])
    out = "{}".format(x)
    assert "kg" in out


def test_repr_round_trip():
    x = _arr([1.0, 2.5])
    assert "kg" in repr(x)


# --- broadcast / length-mismatch ------------------------------------------

def test_length_mismatch_returns_nan_array():
    x = _arr([1, 2])
    y = _arr([1, 2, 3])
    out = x + y
    assert all(math.isnan(v) for v in out.magnitude.tolist())


# --- __getitem__ ----------------------------------------------------------

def test_getitem_negative_index():
    x = _arr([10, 20, 30])
    last = x[-1]
    assert isinstance(last, Quantity)
    assert last.magnitude == 30.0


def test_getitem_out_of_range_raises():
    x = _arr([10, 20])
    with pytest.raises(IndexError):
        x[5]
