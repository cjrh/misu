"""Negative-path tests covering error branches in the engine.

Each test exercises a single error path through the Python API. Where
possible, error-class assertions are kept loose (`Exception`) because
PyO3 maps several of its error types to Python's base exception class.
"""
import numpy as np
import pytest

from misu import (
    EIncompatibleUnits,
    Quantity,
    QuantityNP,
    addType,
    kg,
    m,
    quantity_from_string,
    s,
    dimensionless,
)


# --- parser -----------------------------------------------------------------

def test_parser_bad_number():
    with pytest.raises(ValueError):
        quantity_from_string("abc m")


def test_parser_unknown_unit():
    with pytest.raises(ValueError):
        quantity_from_string("1 zorblax")


def test_parser_empty_unit_symbol():
    with pytest.raises(ValueError):
        quantity_from_string("1 ^2")


def test_parser_bad_exponent():
    with pytest.raises(ValueError):
        quantity_from_string("1 m^x")


# --- Quantity construction & invariants -------------------------------------

def test_quantity_unit_list_must_have_length_7():
    with pytest.raises(ValueError):
        Quantity(1.0, [1, 0, 0])


def test_quantity_pow_with_quantity_exponent_rejected():
    with pytest.raises(AssertionError):
        (2 * m) ** (3 * kg)


def test_quantity_float_only_dimensionless():
    with pytest.raises(AssertionError):
        float(2 * kg)


def test_quantity_setunit_is_frozen():
    with pytest.raises(AssertionError):
        (2 * kg).setunit([0, 0, 0, 0, 0, 0, 0])


def test_quantity_setvaldict_is_frozen():
    with pytest.raises(AssertionError):
        (2 * kg).setValDict({})


def test_quantity_unit_category_undefined():
    # kg^5 * m^3 has no registered category name
    with pytest.raises(Exception):
        (kg ** 5 * m ** 3).unitCategory()


# --- math on non-dimensionless ---------------------------------------------

def test_quantity_math_fn_on_non_dimensionless_raises():
    with pytest.raises(EIncompatibleUnits):
        (2 * kg).sin()


def test_np_sin_on_non_dimensionless_quantity_raises():
    # np.sin forwards to Quantity.sin() via __array_priority__.
    with pytest.raises(EIncompatibleUnits):
        np.sin(2 * kg)


# --- addType ---------------------------------------------------------------

def test_addtype_double_register_rejected():
    # Use kg^9 — not in the catalogue, so we can register without conflict.
    q = kg ** 9
    addType(q, "Test_kg9_a")
    with pytest.raises(Exception):
        addType(q, "Test_kg9_b")


# --- setRepresent ---------------------------------------------------------

def test_setrepresent_requires_target_or_fn():
    with pytest.raises(Exception):
        (1 * kg).setRepresent()


# --- QuantityNP error paths ------------------------------------------------

def test_quantity_np_incompatible_units_addition():
    x = np.array([1, 2]) * kg
    y = np.array([1, 2]) * s
    with pytest.raises(EIncompatibleUnits):
        x + y


def test_quantity_np_coerce_2d_array_raises():
    # 2-D arrays cannot be cast into PyArray1<f64>.
    arr2d = np.array([[1.0, 2.0], [3.0, 4.0]])
    with pytest.raises(TypeError):
        QuantityNP(arr2d)
