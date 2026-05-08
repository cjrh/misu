import numpy as np

from misu import m, QuantityNP, Quantity


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

