misu
====

| ``misu`` is short for "misura",
| which means **measurement** (in Italian).

Demo
----

Demo to go here.

Introduction
------------

| ``misu`` is a package of handling physical quantities
| with dimensions. This means performing calculations
| with all the units being tracked correctly. It is
| possible to add *kilograms per hour* to
| *ounces per minute*, obtain the correct answer, and
| have that answer be reported in, say, *pounds per
week*.

| ``misu`` grew out of a personal need. I have used this code
| personally in a (chemical) engineering context for
| well over a year now (at time of writing, Feb 2015).
| Every feature has been added in response to a personal need.

Features
^^^^^^^^

-  Written as a Cython extension module (for speed).
    Speed benefits carry over when using
   ``misu`` from your own Cython module (a ``.pxd`` is
   provided for linking).
-  Decorators for functions to enforce dimensions
   \`\`\`python
   @dimensions(x=Length, y=Mass)
   def f(x, y):
    return x/y

| f(2\ *m, 3*\ kg) # Works
| f(200\ *feet, 3*\ tons) # Works

| f(2\ *joules, 3*\ kelvin) # raises UnitsError
| f(2\ *m, 3) # raises UnitsError
``- An operator for easily stripping the units  component to obtain a plain numerical value``\ python
mass = 100 * kg
| mass\_lb = mass >> lb

| duty = 50 \* MW
| duty\_BTU\_hr = duty >> BTU / hr
| \`\`\ ``- An enormous amount of redundancy in the naming of various units. This means that``\ m\ ``,``\ metre\ ``,``\ metres\ ``,``\ METRE\ ``,``\ METRES\ ``will all work.  The reason for this is that from my own experience, when working interactively (e.g. in the IPython Notebook) it can be very distracting to incorrectly guess the name for a particular unit, and have to look it up.``\ ft\ ``,``\ foot\ ``and``\ feet\ ``all work,``\ m3\ ``means``\ m\*\*3\`
and
| so on.

-  You can specify a *reporting unit* for a dimension,
   meaning that you could have all lengths be reported
   in "feet" by default for example.
-  You can specify a *reporting format* for a particular
   unit.

There are other projects, why ``misu``?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

| There are several units systems for Python, but the primary motivating
use-case is that ``misu`` is
| written as a Cython module and is by far the fastest\*
| for managing units available in Python.

\*\ *Except for ``NumericalUnits``, which is a special case*

\*\*\ *I haven't actually checked that this statement is true for all of
them yet.*

General usage
-------------

| For speed-critical code, the application of unit operations can still
be too slow.
| In these situations it is typical to first cast quantities into
numerical values
| (doubles, say), perform the speed-critical calculations (perhaps call
into a
| C-library), and then re-cast the result back into a quantity and
return that from
| a function.

.. code:: python

    @dimensions(x = Length, y = Mass):
    def f(x, y):
        x = x >> metre
        y = y >> ounces
        <code that assumes meters and ounces, returns value in BTU>
        return answer * BTU 

| This way you can still easily wrap performance-critical calculations
with
| robust unit-handling.

Inspiration
^^^^^^^^^^^

| The inspiration for ``misu`` was
`Frink <http://futureboy.us/frinkdocs/>`__
| by Alan Eliasen. It is *wonderful*, but I need to work
| with units in the IPython Notebook, and with all my
| other Python code.

| There are a bunch of other similar projects. I have not used any
| of them enough yet to provide a fair comparison:

-  `astropy.units <>`__
-  `Buckingham <>`__
-  `DimPy <>`__
-  `Magnitude <>`__
-  `NumericalUnits <>`__
-  `Pint <>`__
-  `Python-quantities <>`__
-  `Scalar <>`__
-  `Scientific.Physics.PhysicalQuantities <>`__
-  `SciMath <>`__
-  `sympy.physics.units <>`__
-  `udunitspy <>`__
-  `Units <>`__
-  `Unum <>`__

