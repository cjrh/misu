from __future__ import print_function

import os
import sys


sys.path.insert(0, os.path.abspath(".."))

introduction = """

misu - physical quantities (units) in Python.

README

There are already several other unit conversion modules
available for python, including:
    - scipy.physics.units
    - Quantities
    - Unum
    - magnitude
    - Pint
    - Units

misu does not appear at this stage to be any better than any
of the other options.  However, all parents should love their
children regardless.

I have always used frink (a java-based units-aware programming
language interpreter), but I wanted a system of tagging my
own python functions with requirements for specific physical
quantities, just like frink allows.

So, for example, a dimensionless number that occurs
frequently in chemical engineering is the Reynolds number and
is defined as

    Re = density * velocity * length / viscosity

Clearly, it will only be perfectly dimensionless if all the
arguments have compatible units.  I wanted to be able to do
this in code:

    @unit_signature(rho='Mass density', v='Velocity',
                    L='Length', mu='Dynamic viscosity')
    def Reynolds_number(rho, v, L, mu):
        return rho * v * L / mu

and have the results *always* be perfectly dimensionless.
Furthermore, if the user supplied a value for one of the
arguments that did not satisfy the required type of physical
quantity, then an exception would be thrown.

With this target in mind, misu was born.

Demonstrations
=============="""

lines = """
# Create a new variable to store pressure:

P = 2000 * kPa

# Convert the value to bars:

print P.convert(bar)

# Perhaps we want to always have pressures reported in MPa (megapascals):

P.setRepresent(MPa, 'MPa')
print P

# This changes the presentation of *all* pressures:

print 200*bar + 7600*mmHg
print 5000*kPa - 50e3*N/m2

# Lengths!

my_length = 10*inch + 50*cm + 0.25*foot - 0.5*m
print my_length.convert(mm)

# Temperatures can be declared only in absolute units like
# kelvin (K) or rankine (R), but it is easy to create a
# representation for reporting temperatures.

temp = 273.15 * K
print temp
temp.setRepresent(convert_function=lambda _, mag: mag - 273.15, symbol='C')
print temp
temp = temp + 100*K
print temp

# Only absolute temperatures are defined as declarable units though.

temp = 100*K+100*R

# But note that the answer continues to come out as we
# required earlier (degrees C):

print temp

# We could changed the representation to something else:
temp.setRepresent(convert_function=lambda _, mag: (mag - 273.15)*9./5.+32, symbol='F')
print temp
# We know that -40F == -40C so...
temp = 273.15*K - 40*K
print temp

# Energy

energy = 100*J
print 'energy = {}'.format(energy)
energy.setRepresent(as_unit=J, symbol='J')
print 'energy = {}'.format(energy)
# Format strings also work correctly.
energy.setRepresent(BTU, 'BTU')
print '{:.3e}'.format(energy)

# It is easy to examine the details:

print energy.magnitude
print energy.units()

# You can see that internally, the vars store fundamental SI unit exponents.

print energy**2
print (energy**2).units()

# The type is obviously examinable:

print type(energy)

# The size is reasonably compact:
import sys
print sys.getsizeof(energy)

# Units can also be dimensionless:

print 1*dimensionless

# Decorators
############

"""

decorators = """

"""

print(introduction)

from misu import *
for x in lines.split('\n'):
    if len(x.strip()) == 0:
        print('')
        continue
    if x[0] == '#':
        print(x[1:].strip())
    else:
        print('>>> ' + x)
        exec(x)
