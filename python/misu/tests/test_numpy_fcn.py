# Uses py.test.
from __future__ import print_function
import os
import sys

new_syspath = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.append(new_syspath)

import math
import numpy as np
import pytest

from misu import (
    kg, s, lb, minute, Hz, kHz, GHz, MHz, ft, BTU, MW, d, m3, inch, Pa, bar,
    cm, minutes, hr, m, dimensionless
)
from misu import EIncompatibleUnits, dimensions, QuantityNP, Quantity, quantity_from_string

import numpy
try:
    numpy.set_printoptions(formatter=dict(all=lambda x: '{:.3g}'.format(x)))
except:
    pass



def lookup_type(quantity):
    return 'Quantity: {} Type: {}'.format(quantity, quantity.unitCategory())


a_m = np.linspace(1,2)
a = a_m * m
b_m = 3
b = b_m*m
c_m = 1
c = c_m*m

def test_type_1():
    assert type(np.sin(a/b)) == QuantityNP

def test_type_2():
    assert type(np.sin(b/c)) == Quantity

def test_sin_1():
    assert np.sin(a/b).magnitude[0] == np.sin(a_m/b_m)[0]

def test_sin_2():
    assert np.sin(c/b).magnitude == np.sin(c_m/b_m)

