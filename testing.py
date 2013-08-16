from unity import *

import unittest

class TestOperations(unittest.TestCase):
    pass

print
print '*'*80
print
def test(text):
    '''Utility function for pretty-print test output.'''
    try:
        print '{:50}: {}'.format(text, eval(text))
    except:
        print
        print 'Trying: ' + text
        print traceback.format_exc()
        print

a = 2.5 * kg / s
b = 34.67 * kg / s

test('a')
test('b')
test('a+b')
test('a-b')
test('a*b')
test('a/b')

test('2.0 * m + 3.0 * kg')
test('2.0 * kg / s * 3.0')
test('2.0 * 3.0 * kg / s')

test('(1.0/m)**0.5')

test('((kg ** 2.0)/(m))**0.5')
test('(1.56724 * (kg ** 2.0)/(m * (s**2.0)))**0.5')

############################################################################

from sys import getsizeof
print getsizeof(a)

print
print 'Testing Quantities'
print '=================='
print
#print 'QuantityType = {}'.format(QuantityType)
#print 'Quantity Type of m is {}'.format(QuantityType[m.unit])
print
print 'Hz = {}'.format(Hz)
print 'kHz = {}'.format(kHz)
print 'MHz = {}'.format(MHz)
print 'GHz = {}'.format(GHz)

def pbrk():
    print
    print '='*20
    print
pbrk()

def lookupType(quantity):
    print 'Quantity: {} Type: {}'.format(quantity, quantity.unitCategory())

lookupType(BTU)
lookupType(lb)
lookupType(200 * MW * 10 * d)
#import pdb; pdb.set_trace()
J.setRepresent(as_unit=GJ, symbol='GJ')
lookupType(200 * MW * 10 * d)

#########################################D:\Dropbox\Technical\codelibs\workspace\ipython_notebooks###################################

pbrk()
print 'Example calculations:'
pbrk()

mass = 200*lb
#import pdb; pdb.set_trace()
print 'mass = {}'.format(mass)
flowrate = 40*mg/s
print 'flowrate = {}'.format(flowrate)
s.setRepresent(as_unit=d, symbol='days')
print 'Time required to make final mass = {}'.format(mass / flowrate)

############################################################################

pbrk()
print 'Checking the function decorator'
pbrk()

@unit_signature(rho='Mass density', v='Velocity', L='Length', mu='Dynamic viscosity')
def Reynolds_number(rho, v, L, mu):
    return rho * v * L / mu

data=dict(rho=1000*kg/m3, v=12*m/s, L=5*inch, mu=1e-3*Pa*s)
print 'Re = {}'.format(Reynolds_number(**data))

data=dict(rho=1000*kg/m3, v=12*m/s, L=1.5*inch, mu=1.011e-3*Pa*s)
Re = Reynolds_number(**data)
print 'Re = {:.2e}'.format(Reynolds_number(**data))

@unit_signature(roughness='Length', Dh='Length', Re='Dimensionless')
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

@unit_signature(roughness='Length', Dh='Length', Re='Dimensionless')
def friction_factor_Colebrook_Haaland(roughness, Dh, Re):
    K = roughness.convert(m) / Dh.convert(m)
    tmp = math.pow(K/3.7, 1.11) + 6.9 / Re
    inv = -1.8 * math.log10(tmp)
    return dimensionless * (1./inv)**2

f = friction_factor_Colebrook(1e-6*m, 1.5*inch, Re)
fH = friction_factor_Colebrook_Haaland(1e-6*m, 1.5*inch, Re)
print 'At Re = {}, friction factor = {}'.format(Re, f)
print 'At Re = {}, friction factorH = {}'.format(Re, fH)
if isinstance(f, Quantity):
    print 'f.unitCategory() = {}'.format(f.unitCategory())
if isinstance(fH, Quantity):
    print 'fH.unitCategory() = {}'.format(fH.unitCategory())


@unit_signature(
    fD='Dimensionless', D='Length', rho='Mass density', v='Velocity', L='Length')
def pressure_drop(fD, D, rho, v, L=1*m):
    '''Arguments are
        fD:  Darcy-Weisbach friction factor
        L:   Length of pipe (default 1 metre)
        D:   Diameter of pipe
        rho: Density of the fluid
        v:   Velocity of the fluid
    '''
    return fD * L / D * rho * v**2 / 2

flow = 1*m3/s
m.setRepresent(as_unit=inch, symbol='"')
Pa.setRepresent(as_unit=bar, symbol='bar')
for D in [x*inch for x in range(1,11)]:
    v = flow / D**2 / math.pi * 4
    rho = 1000*kg/m3
    Re = Reynolds_number(rho=rho, v=v, L=D, mu=1e-3*Pa*s)
    f = friction_factor_Colebrook(1e-5*m, D, Re)
    print 'Pressure drop at diameter {} = {}'.format(
        D, pressure_drop(f,D,rho, v, L=1*m))

pbrk()
print 'Few more checks'
pbrk()

v = 101*m/s
print '101 m/s -> ft/hr = {}'.format(v.convert(ft/hr))

dbg=1
import numpy as np
x = np.array([1,2,3])


