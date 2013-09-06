# Uses py.test.

import pytest
from unity import *
import numpy as np

a = 2.5 * kg / s
b = 34.67 * kg / s

def lookupType(quantity):
    return 'Quantity: {} Type: {}'.format(quantity, quantity.unitCategory())

class TestClass:
    def test_representation(self):
        assert repr(a) == '9000 kg/hr'
        assert repr(b) == '1.248e+05 kg/hr'

    def test_format_simple(self):
        assert '{:.2f}'.format(b)    == '124812.00 kg/hr'

    def test_format_left_align(self):
        fmtstr = '{:<20.2f}'.format(b)
        assert fmtstr == '124812.00 kg/hr     '

    def test_format_right_align(self):
        fmtstr = '{:>20.2f}'.format(b)
        assert fmtstr == '     124812.00 kg/hr'

    def test_addition(self):
        assert repr(a + b) == '1.338e+05 kg/hr'

    def test_subtraction(self):
        assert repr(a - b) == '-1.158e+05 kg/hr'

    def test_multiplication(self):
        assert repr(a * b) == '86.675 kg^2.0 s^-2.0'

    def test_division(self):
        assert repr(a / b) == '0.0721084511105'

    def test_incompatible_units(self):
        with pytest.raises(EIncompatibleUnits) as E:
            print 2*m
            x = 2.0*m + 3.0*kg
        print E.value.message
        assert E.value.message == 'Incompatible units: 2 m and 3 kg'

    def test_operator_precedence(self):
        assert repr(2.0 * kg / s * 3.0) == '2.16e+04 kg/hr'
        assert repr(2.0 * 3.0 * kg / s) == '2.16e+04 kg/hr'
        assert repr((1.0/m)**0.5) == '1.0 m^-0.5'

        assert repr(((kg ** 2.0)/(m))**0.5) == '1.0 m^-0.5 kg^1.0'
        assert repr((1.56724 * (kg ** 2.0)/(m * (s**2.0)))**0.5) ==  '1.25189456425 m^-0.5 kg^1.0 s^-1.0'

    def test_si_prefixes(self):
        assert 'Hz = {}'.format(Hz) == 'Hz = 1 Hz'
        assert 'kHz = {}'.format(kHz) == 'kHz = 1000 Hz'
        assert 'MHz = {}'.format(MHz) == 'MHz = 1e+06 Hz'
        assert 'GHz = {}'.format(GHz) == 'GHz = 1e+09 Hz'

    def test_conversions(self):
        assert 1*m >> ft == 3.280839895013123

    def test_unit_category(self):
        assert lookupType(BTU) == 'Quantity: 1054 J Type: Energy'
        assert lookupType(lb) == 'Quantity: 0.4536 kg Type: Mass'
        assert lookupType(200*MW * 10*d) == 'Quantity: 1.728e+14 J Type: Energy'
        #J.setRepresent(as_unit=GJ, symbol='GJ')
        #assert lookupType(200*MW * 10*d)

    def test_func_decorator1(self):
        ''' This tests the function decorator on Reynolds number,
        a standard dimensionless number in process engineering.'''

        # Function definition
        @dimensions(rho='Mass density', v='Velocity', L='Length', mu='Dynamic viscosity')
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
            for i in range(2): # two iterations
                ej = (zj + math.log(x1 + zj) - x2) / (1. + x1 + zj)
                tol = (1. + x1 + zj + (1./2.)*ej) * ej * (x1 + zj) / (1. + x1 + zj + ej + (1./3.)*ej**2)
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
        assert 'At Re = {}, friction factor = {}'.format(Re, f) == 'At Re = 452225.519288, friction factor = 0.0137489883857'
        assert 'At Re = {}, friction factorH = {}'.format(Re, fH) == 'At Re = 452225.519288, friction factorH = 0.0135940052381'

        assert 'f.unitCategory() = {}'.format(f.unitCategory()) == 'f.unitCategory() = Dimensionless'
        assert 'fH.unitCategory() = {}'.format(fH.unitCategory()) == 'fH.unitCategory() = Dimensionless'

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
        for D in [x*inch for x in range(1,11)]:
            v = flow / D**2 / math.pi * 4
            rho = 1000*kg/m3
            Re = Reynolds_number(rho=rho, v=v, L=D, mu=1e-3*Pa*s)
            f = friction_factor_Colebrook(1e-5*m, D, Re)
            lines.append('Pressure drop at diameter {} = {}'.format(
                D, pressure_drop(f,D,rho, v, L=1*m)))

        # Spot checks
        assert lines[0] == 'Pressure drop at diameter 1 " = 1.215e+04 bar'
        assert lines[4] == 'Pressure drop at diameter 5 " = 2.865 bar'
        assert lines[9] == 'Pressure drop at diameter 10 " = 0.08282 bar'

    def test_func_decorator2(self):
        # Working only in m
        m.setRepresent(as_unit=m, symbol='m')

        @dimensions(x='Length')
        def f(x,y,z):
            return x*y*z

        assert f(12*cm, 1, 1) == 0.12*m

        @dimensions(y='Length')
        def f(x,y,z):
            return x*y*z

        assert f(1, 12*cm, 1) == 0.12*m

        @dimensions(z='Length')
        def f(x,y,z):
            return x*y*z

        assert f(1, 1, 12*cm) == 0.12*m

    def test_numpy_basic(self):
        x = np.array([1,2,3]) * kg
        assert repr(x) == '[ 1.  2.  3.] kg'

    def test_numpy_operations(self):
        x = np.array([1,2,3]) * kg
        y = x / (20*minutes)
        assert repr(y) == '[ 3.  6.  9.] kg/hr'
        assert repr(y**2) == '[  6.94444444e-07   2.77777778e-06   6.25000000e-06] kg^2.0 s^-2.0'


