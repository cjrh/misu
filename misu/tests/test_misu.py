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


a = 2.5 * kg / s
b = 34.67 * kg / s


def lookup_type(quantity):
    return 'Quantity: {} Type: {}'.format(quantity, quantity.unitCategory())


def test_representation():
    assert repr(a) == '9000 kg/hr'
    assert repr(b) == '1.248e+05 kg/hr'


def test_format_simple():
    assert '{:.2f}'.format(b) == '124812.00 kg/hr'


@pytest.mark.xfail(reason='This requires further work.')
def test_format_left_align():
    fmtstr = '{:<20.2f}'.format(b)
    assert fmtstr == '124812.00 kg/hr     '


@pytest.mark.xfail(reason='This requires further work.')
def test_format_right_align():
    fmtstr = '{:>20.2f}'.format(b)
    assert fmtstr == '     124812.00 kg/hr'


def test_from_string1():
    quantity_from_string('1 m^2 s^-1') == 1 * m**2/s


def test_from_string2():
    quantity_from_string('1 m^2     s^-1') == 1 * m**2/s


def test_from_string3():
    assert quantity_from_string('-1.158e+05 m/s kg^6.0') == -1.158e+05* m/s* kg**6.0


def test_addition():
    assert repr(a + b) == '1.338e+05 kg/hr'


def test_subtraction():
    assert repr(a - b) == '-1.158e+05 kg/hr'


def test_multiplication():
    assert '{:.3f}'.format(a * b) == '86.675 kg^2.0 s^-2.0'


def test_division():
    assert '{:.5f}'.format(a / b) == '0.07211'


def test_comparison_smaller():
    assert 1*m < 2*m

def test_comparison_smaller_equal():
    assert 3*m <= 3*m

def test_comparison_equal():
    assert 3*m == 3*m

def test_comparison_larger():
    assert 3*m > 2*m

def test_comparison_larger_equal():
    assert 3*m >= 3*m

def test_comparison_equal():
    assert 3*m == 3*m

def test_incompatible_units():
    with pytest.raises(EIncompatibleUnits) as E:
        print(2*m)
        x = 2.0*m + 3.0*kg
    print(str(E.value))
    assert str(E.value) == 'Incompatible units: 2 m and 3 kg'


def test_operator_precedence():
    assert repr(2.0 * kg / s * 3.0) == '2.16e+04 kg/hr'
    assert repr(2.0 * 3.0 * kg / s) == '2.16e+04 kg/hr'
    assert repr((1.0/m)**0.5) == '1.0 m^-0.5'

    assert repr(((kg ** 2.0)/(m))**0.5) == '1.0 m^-0.5 kg^1.0'
    # assert repr((1.56724 * (kg ** 2.0)/(m * (s**2.0)))**0.5) \
    assert '{:.2f}'.format((1.56724 * (kg ** 2.0)/(m * (s**2.0)))**0.5) \
        == '1.25 m^-0.5 kg^1.0 s^-1.0'


def test_si_prefixes():
    assert 'Hz = {}'.format(Hz) == 'Hz = 1 Hz'
    assert 'kHz = {}'.format(kHz) == 'kHz = 1000 Hz'
    assert 'MHz = {}'.format(MHz) == 'MHz = 1e+06 Hz'
    assert 'GHz = {}'.format(GHz) == 'GHz = 1e+09 Hz'


def test_conversions():
    assert 1*m >> ft == 3.280839895013123


def test_unit_category():
    assert lookup_type(BTU) == 'Quantity: 1054 J Type: Energy'
    assert lookup_type(lb) == 'Quantity: 0.4536 kg Type: Mass'
    assert lookup_type(200 * MW * 10 * d) \
           == 'Quantity: 1.728e+14 J Type: Energy'
    #J.setRepresent(as_unit=GJ, symbol='GJ')
    #assert lookup_type(200*MW * 10*d)


def test_func_decorator1():
    """ This tests the function decorator on Reynolds number,
    a standard dimensionless number in process engineering."""

    # Function definition
    @dimensions(rho='Mass density', v='Velocity', L='Length',
                mu='Dynamic viscosity')
    def Reynolds_number(rho, v, L, mu):
        return rho * v * L / mu

    # Test 1
    data = dict(
        rho=1000*kg/m3,
        v=12*m/s,
        L=5*inch,
        mu=1e-3*Pa*s)
    assert 'Re = {}'.format(Reynolds_number(**data)) == 'Re = 1524000.0'

    # Test 2
    data = dict(
        rho=1000*kg/m3,
        v=12*m/s,
        L=1.5*inch,
        mu=1.011e-3*Pa*s)
    Re = Reynolds_number(**data)
    assert 'Re = {:.2e}'.format(Re) == 'Re = 4.52e+05'

    # Friction factor is another engineering quantity.
    # The Colebrook equation requires iteration, but there
    # are various approximations to the Colebrook equation
    # that do not require iteration, like Haaland below.
    @dimensions(roughness='Length', Dh='Length', Re='Dimensionless')
    def friction_factor_Colebrook(roughness, Dh, Re):
        '''Returns friction factor.
        http://hal.archives-ouvertes.fr/docs/00/33/56/55/PDF/fast_colebrook.pdf
        '''
        K = roughness.convert(m) / Dh.convert(m)
        l = math.log(10)
        x1 = l * K * Re / 18.574
        x2 = math.log(l * Re.magnitude / 5.02)
        zj = x2 - 1./5.
        # two iterations
        for i in range(2):
            ej = (zj + math.log(x1 + zj) - x2) / (1. + x1 + zj)
            tol = (1. + x1 + zj + (1./2.)*ej) * ej * (x1 + zj) \
                / (1. + x1 + zj + ej + (1./3.)*ej**2)
            zj = zj - tol

        return (l / 2.0 / zj)**2

    @dimensions(roughness='Length', Dh='Length', Re='Dimensionless')
    def friction_factor_Colebrook_Haaland(roughness, Dh, Re):
        K = roughness.convert(m) / Dh.convert(m)
        tmp = math.pow(K/3.7, 1.11) + 6.9 / Re
        inv = -1.8 * math.log10(tmp)
        return dimensionless * (1./inv)**2

    f = friction_factor_Colebrook(1e-6*m, 1.5*inch, Re)
    fH = friction_factor_Colebrook_Haaland(1e-6*m, 1.5*inch, Re)
    assert 'At Re = {:.2f}, friction factor = {:.5f}'.format(Re, f) \
        == 'At Re = 452225.52, friction factor = 0.01375'
    assert 'At Re = {:.2f}, friction factorH = {:.5f}'.format(Re, fH) \
        == 'At Re = 452225.52, friction factorH = 0.01359'

    assert 'f.unitCategory() = {}'.format(f.unitCategory()) \
        == 'f.unitCategory() = Dimensionless'
    assert 'fH.unitCategory() = {}'.format(fH.unitCategory()) \
        == 'fH.unitCategory() = Dimensionless'

    # The friction factor can then be used to calculate the
    # expected drop in pressure produced by flow through a
    # pipe.
    @dimensions(
        fD='Dimensionless',
        D='Length',
        rho='Mass density',
        v='Velocity',
        L='Length')
    def pressure_drop(fD, D, rho, v, L=1*m):
        '''Arguments are
            fD:  Darcy-Weisbach friction factor
            L:   Length of pipe (default 1 metre)
            D:   Diameter of pipe
            rho: Density of the fluid
            v:   Velocity of the fluid
        '''
        return fD * L / D * rho * v**2 / 2

    # Test the pressure drop
    flow = 1*m3/s
    m.setRepresent(as_unit=inch, symbol='"')
    Pa.setRepresent(as_unit=bar, symbol='bar')
    lines = []
    for D in [x*inch for x in range(1, 11)]:
        v = flow / D**2 / math.pi * 4
        rho = 1000*kg/m3
        Re = Reynolds_number(rho=rho, v=v, L=D, mu=1e-3*Pa*s)
        f = friction_factor_Colebrook(1e-5*m, D, Re)
        lines.append('Pressure drop at diameter {} = {}'.format(
            D, pressure_drop(f, D, rho, v, L=1*m)))

    # Spot checks
    assert lines[0] == 'Pressure drop at diameter 1 " = 1.215e+04 bar'
    assert lines[4] == 'Pressure drop at diameter 5 " = 2.865 bar'
    assert lines[9] == 'Pressure drop at diameter 10 " = 0.08282 bar'


def test_func_decorator2():
    # Working only in m
    m.setRepresent(as_unit=m, symbol='m')

    @dimensions(x='Length')
    def f(x, y, z):
        return x*y*z

    assert f(12*cm, 1, 1) == 0.12*m

    @dimensions(y='Length')
    def f(x, y, z):
        return x*y*z

    assert f(1, 12*cm, 1) == 0.12*m

    @dimensions(z='Length')
    def f(x, y, z):
        return x*y*z

    assert f(1, 1, 12*cm) == 0.12*m


def test_numpy_basic():
    x = np.array([1, 2, 3]) * kg
    assert repr(x) == '[1 2 3] kg'


def test_numpy_operations():
    x = np.array([1, 2, 3]) * kg
    y = x / (20*minutes)
    assert repr(y) == '[3 6 9] kg/hr'
    assert repr(y**2) \
        == '[6.94e-07 2.78e-06 6.25e-06] kg^2.0 s^-2.0'


def test_npclass():
    x = np.array([1.0, 2.0, 3.0])
    y = QuantityNP(x) * kg
    assert repr(y) == '[1 2 3] kg'


def test_numpy_addition():
    x = np.array([1, 2, 3]) * kg
    y = np.array([1, 2, 3]) * lb
    assert repr(x+y) == '[1.45 2.91 4.36] kg'
    lbval = x+y >> lb
    assert np.allclose(lbval,
        np.array([3.20462262,  6.40924524,  9.61386787]))


def test_numpy_subtraction():
    x = np.array([1, 2, 3]) * kg
    y = np.array([1, 2, 3]) * lb
    assert repr(x-y) == '[0.546 1.09 1.64] kg'


def test_numpy_slice():
    x = np.array([ 0.08400557, 0.19897197, 0.12407021, 0.11867142]) * kg/hr
    assert repr(x[:2]) == '[0.084 0.199] kg/hr'
    assert repr(x[3]) == '0.1187 kg/hr'
