misu
====

`misu` is short for "misura", 
which means **measurement** (in Italian).

Introduction
------------

`misu` is a package of handling physical quantities
with dimensions. This means performing calculations
with all the units being tracked correctly. It is 
possible to add *kilograms per hour* to 
*ounces per minute*, obtain the correct answer, and 
have that answer be reported in, say, *pounds per 
week*.

`misu` grew out of a personal need. I have used this code
personally in an engineering context for
well over a year now (at time of writing, Feb 2015).
Every feature has been added in response to a personal need.

#### Features

- Written as a Cython extension module (for speed).
 Speed benefits carries over when using
`misu` from your own Cython module (a `.pxd` is 
provided for linking).
- Decorators for functions to enforce dimensions
```python
@dimensions(x=Length, y=Mass)
def f(x, y):
    return x/y

f(2*m, 3*kg)         # Works
f(200*feet, 3*tons)  # Works

f(2*joules, 3*kelvin)  # raises UnitsError
f(2*m, 3)                # raises UnitsError
```
- An operator for easily stripping the units 
component to obtain a numerical value
```python
mass = 100 * kg
mass_lb = mass >> lb

duty = 50 * MW
duty_BTU_hr = duty >> BTU / hr
```
- An enormous amount of redundancy in the naming
of various units. This means that `m`, `metre`, 
`metres`, `METRE`, `METRES` will all work.
 The reason for this is that
from my own experience, when working interactively
(e.g. in the IPython Notebook) it can be very
distracting to incorrectly guess the name for a
particular unit, and have to look it up.
- You can specify a *reporting unit* for a dimension, 
meaning that you could have all lengths be reported
in "feet" by default for example.
- You can specify a *reporting format* for a particular
unit.

Demo
----

Demo to go here.

#### There are other projects, why `misu`?

There are several units systems for Python, but the primary motivating use-case is that `misu` is
written as a Cython module and is by far the fastest*
for managing units available in Python. 

\**Except for `NumericalUnits`, which is a special case*

\*\**I haven't actually checked that this statement is true for all of them yet.*

#### Inspiration

The inspiration for `misu` was [Frink](http://futureboy.us/frinkdocs/)
by Alan Eliasen. It is wonderful, but I need to work
with units in the IPython Notebook, and with all my
other Python code.

There are a bunch of other similar projects:

- [astropy.units]("http://astropy.readthedocs.org/en/latest/units/")
- [Buckingham]("http://code.google.com/p/buckingham/")
- [DimPy]("http://www.inference.phy.cam.ac.uk/db410/")
- [Magnitude]("http://juanreyero.com/open/magnitude/")
- [NumericalUnits]("https://pypi.python.org/pypi/numericalunits")
- [Pint]("http://pint.readthedocs.org/")
- [Python-quantities]("https://pypi.python.org/pypi/quantities")
- [Scalar]("http://russp.us/scalar-guide.htm")
- [Scientific.Physics.PhysicalQuantities]("http://dirac.cnrs-orleans.fr/ScientificPython/ScientificPythonManual/Scientific.Physics.PhysicalQuantities-module.html")
- [SciMath]("http://scimath.readthedocs.org/en/latest/units/intro.html")
- [sympy.physics.units]("http://docs.sympy.org/dev/modules/physics/units.html")
- [udunitspy]("https://github.com/blazetopher/udunitspy")
- [Units]("https://bitbucket.org/adonohue/units/")
- [Unum]("https://bitbucket.org/kiv/unum/")


