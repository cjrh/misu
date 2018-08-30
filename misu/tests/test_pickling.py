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
from misu import EIncompatibleUnits, dimensions, QuantityNP, quantity_from_string

import numpy
try:
    numpy.set_printoptions(formatter=dict(all=lambda x: '{:.3g}'.format(x)))
except:
    pass

import pickle

a = 2.5 * kg / s
b = 34.67 * kg / s


def lookup_type(quantity):
    return 'Quantity: {} Type: {}'.format(quantity, quantity.unitCategory())

def test_pickle():
    var = 2.5 * kg / s
    pick = pickle.dumps(var)
    res = pickle.loads(pick)
    assert var==res

def test_pickle_np():
    var = np.array([2.5, 4]) * kg / s
    pick = pickle.dumps(var)
    res = pickle.loads(pick)
    assert (var[0]==res[0] and var[1]==res[1])
