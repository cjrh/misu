.. image:: https://github.com/cjrh/misu/actions/workflows/ci.yml/badge.svg?branch=master
    :target: https://github.com/cjrh/misu/actions/workflows/ci.yml

.. image:: https://coveralls.io/repos/github/cjrh/misu/badge.svg?branch=master
    :target: https://coveralls.io/github/cjrh/misu?branch=master

.. image:: https://img.shields.io/pypi/pyversions/misu.svg
    :target: https://pypi.python.org/pypi/misu

.. image:: https://img.shields.io/github/tag/cjrh/misu.svg
    :target: https://img.shields.io/github/tag/cjrh/misu.svg

.. image:: https://img.shields.io/pypi/v/misu.svg
    :target: https://img.shields.io/pypi/v/misu.svg

misu
====

``misu`` is short for "misura", which means **measurement** (in
Italian). ``misu`` is a package for doing calculations with in consistent
units of measurement.

Install
-------

Precompiled wheels are published to PyPI for Linux (x86_64, aarch64),
macOS (x86_64, aarch64), and Windows (x64), covering Python 3.9 and
later. There is nothing to compile.

.. code-block:: shell

    uv add misu        # in a uv project
    uv pip install misu
    pip install misu

Demo
----

Most of the time you will probably work with ``misu`` interactively, and
it will be most convenient to import the entire namespace:

.. code:: python

    from misu import *

    mass = 100*kg
    print(mass >> lb)

The symbol ``kg`` got imported from the ``misu`` package. We redefine
the shift operator to perform inline conversions. The code above
produces:

::

    220.46226218487757

There are many units already defined, and it is easy to add more. Here
we convert the same quantity into ounces:

.. code:: python

    print(mass >> oz)

output:

::

    3571.4285714285716

What you see above would be useless on its own. What you really need is
to be able to perform consistent calculations with quantities expressed
in different, but compatible units:

.. code:: python

    mass = 10*kg + 20*lb
    print(mass)

output:

::

    19.07 kg

For addition and subtraction, ``misu`` will ensure that only consistent
units can be used. Multiplication and division will produce new units:

.. code:: python

    distance = 100*metres
    time = 9.2*seconds

    speed = distance / time
    print(speed)

output:

::

    10.87 m/s

As before, it is trivially easy to express that quantity in different
units of compatible dimensions:

.. code:: python

    print(speed >> km/hr)

output:

::

    39.130434782608695

Introduction
------------

``misu`` is a package of handling physical quantities with dimensions.
This means performing calculations with all the units being tracked
correctly. It is possible to add *kilograms per hour* to *ounces per
minute*, obtain the correct answer, and have that answer be reported in,
say, *pounds per week*.

``misu`` grew out of a personal need. I have used this code personally
in a (chemical) engineering context for well over a year now (at time of
writing, Feb 2015). Every feature has been added in response to a
personal need.

Features
^^^^^^^^

-  Speed optimized. ``misu`` is very fast! Heavy math code in Python
   is only around 5X slower when expressed with ``misu`` quantities
   instead of plain floats — see `Performance`_ below for measured
   numbers. This is much faster than other quantities packages for
   Python.

-  Implemented as a Rust extension module via
   `PyO3 <https://pyo3.rs/>`__, so the hot paths run as native code.

-  When an operation involving incompatible units is attempted, an
   ``EIncompatibleUnits`` exception is raised, with a clear explanation
   message about which units were inconsistent.

-  Decorators for functions to enforce dimensions

.. code:: python

    @dimensions(x='Length', y='Mass')
    def f(x, y):
        return x/y

    f(2*m, 3*kg)         # Works
    f(200*feet, 3*tons)  # Works

    f(2*joules, 3*kelvin)  # raises AssertionError
    f(2*m, 3)              # raises AssertionError

-  An operator for easily stripping the units component to obtain a
   plain numerical value

.. code:: python

    mass = 100 * kg
    mass_lb = mass >> lb

    duty = 50 * MW
    duty_BTU_hr = duty >> BTU / hr

-  An enormous amount of redundancy in the naming of various units. This
   means that ``m``, ``metre``, ``metres``, ``METRE``, ``METRES`` will
   all work. The reason for this is that from my own experience, when
   working interactively (e.g. in the IPython Notebook) it can be very
   distracting to incorrectly guess the name for a particular unit, and
   have to look it up. ``ft``, ``foot`` and ``feet`` all work, ``m3``
   means ``m**3`` and so on.
-  You can specify a *reporting unit* for a dimension, meaning that you
   could have all lengths be reported in "feet" by default for example.
-  You can specify a *reporting format* for a particular unit.

Performance
^^^^^^^^^^^

Two looping numerical workloads, each timed in plain Python floats and
then with ``misu`` quantities (so every operation in the inner loop pays
the unit-tracking cost). The benchmark lives at
``scripts/benchmark.py`` and can be re-run any time:

.. code:: shell

    python scripts/benchmark.py

Representative numbers on Python 3.14, best of five runs:

.. list-table::
   :header-rows: 1
   :widths: 55 15 15 15

   * - Workload
     - float (ms)
     - misu (ms)
     - slowdown
   * - ``fall_with_drag`` — 200k Euler steps, 1-D free-fall with
       quadratic drag
     - ~19
     - ~103
     - ~5.2x
   * - ``orbit_step`` — 100k 2-D Kepler steps, sqrt-heavy
     - ~18
     - ~91
     - ~5.1x
   * - **Geometric mean**
     -
     -
     - **~5.1x**

The original 5x heuristic was measured back when ``misu`` was a Cython
extension; the rewrite to a Rust/PyO3 extension lands in the same
ballpark, presumably because the dominant cost is the Python-call
boundary around each ``__mul__`` / ``__add__`` rather than the
unit-arithmetic itself.

There are other projects, why ``misu``?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There are several units systems for Python, but the primary motivating
use-case is that ``misu`` is written as a Rust extension module and is
by far the fastest\* for managing units available in Python.

\*\ *Except for ``NumericalUnits``, which is a special case*

\*\*\ *I haven't actually checked that this statement is true for all of
them yet.*

General usage
-------------

For speed-critical code, the application of unit operations can still be
too slow. In these situations it is typical to first cast quantities
into numerical values (doubles, say), perform the speed-critical
calculations (perhaps call into a C-library), and then re-cast the
result back into a quantity and return that from a function.

.. code:: python

    @dimensions(x='Length', y='Mass')
    def f(x, y):
        x = x >> metre   # Converts to metres, leaving a primitive float
        y = y >> ounces  # Converts to metres, leaving a primitive float
        <code that assumes meters and ounces, returns value in BTU>
        # Convert the primitive float to BTU on the way out
        return answer * BTU

This way you can still easily wrap performance-critical calculations
with robust unit-handling.

Inspiration
^^^^^^^^^^^

The inspiration for ``misu`` was
`Frink <http://futureboy.us/frinkdocs/>`__ by Alan Eliasen. It is
*wonderful*, but I need to work with units in the IPython Notebook, and
with all my other Python code.

There are a bunch of other similar projects. I have not used any of them
enough yet to provide a fair comparison:

-  `astropy.units <http://astropy.readthedocs.org/en/latest/units/>`__
-  `Buckingham <http://code.google.com/p/buckingham/>`__
-  `DimPy <http://www.inference.phy.cam.ac.uk/db410/>`__
-  `Magnitude <http://juanreyero.com/open/magnitude/>`__
-  `NumericalUnits <https://pypi.python.org/pypi/numericalunits>`__
-  `Pint <http://pint.readthedocs.org/>`__
-  `Python-quantities <https://pypi.python.org/pypi/quantities>`__
-  `Scalar <http://russp.us/scalar-guide.htm>`__
-  `Scientific.Physics.PhysicalQuantities <http://dirac.cnrs-orleans.fr/ScientificPython/ScientificPythonManual/Scientific.Physics.PhysicalQuantities-module.html>`__
-  `SciMath <http://scimath.readthedocs.org/en/latest/units/intro.html>`__
-  `sympy.physics.units <http://docs.sympy.org/dev/modules/physics/units.html>`__
-  `udunitspy <https://github.com/blazetopher/udunitspy>`__
-  `Units <https://bitbucket.org/adonohue/units/>`__
-  `Unum <https://bitbucket.org/kiv/unum/>`__

Releasing
---------

Publishing to PyPI is automated via GitHub Actions and `PyPI trusted
publishing <https://docs.pypi.org/trusted-publishers/>`__ (OIDC). No API
tokens or passwords are stored anywhere — PyPI trusts the
``cjrh/misu`` repo's ``release.yml`` workflow running in the ``pypi``
environment, and rejects everything else.

Cutting a release
^^^^^^^^^^^^^^^^^

The version lives in ``Cargo.toml``. ``pyproject.toml`` declares
``dynamic = ["version"]``, so maturin reads it from the Rust crate at
build time — there is only one place to edit.

Use `cargo-release <https://github.com/crate-ci/cargo-release>`__ to
bump, commit, tag, and push in one step. From a clean ``master``:

.. code-block:: shell

    cargo release patch --execute   # 2.0.0 → 2.0.1
    cargo release minor --execute   # 2.0.0 → 2.1.0
    cargo release major --execute   # 2.0.0 → 3.0.0
    cargo release 2.0.5 --execute   # explicit version

Drop ``--execute`` for a dry run.

What happens automatically
^^^^^^^^^^^^^^^^^^^^^^^^^^

cargo-release performs the following steps locally:

1. Bumps ``version`` in ``Cargo.toml`` and updates ``Cargo.lock``.
2. Commits the change with the message ``Release <version>``.
3. Creates an annotated tag ``v<version>``.
4. Pushes the branch and the tag to ``origin``.

The tag push triggers ``.github/workflows/release.yml``, which:

1. Builds wheels for Linux (x86_64, aarch64), macOS (x86_64, aarch64),
   and Windows (x64), plus an sdist. Because PyO3 is configured with
   ``abi3-py39``, one wheel per (OS, arch) covers all supported Python
   versions.
2. Downloads all artifacts into the ``release`` job, which runs in the
   ``pypi`` GitHub environment.
3. Uploads to PyPI via ``pypa/gh-action-pypi-publish``. Authentication
   happens via OIDC against the trusted-publisher configuration on
   PyPI; nothing else is needed.

If the build jobs succeed but the release job fails (for example, the
PyPI environment was not configured), nothing is published, and the
release can be retried by re-running just the failed job.

Troubleshooting
^^^^^^^^^^^^^^^

- **cargo-release refuses with "uncommitted changes"** — commit or
  stash first; cargo-release insists on a clean tree.
- **cargo-release refuses with "not on allowed branch"** — release only
  from ``master`` (the default ``allow-branch`` setting).
- **PyPI rejects the upload with "version already exists"** — PyPI
  filenames are immutable; bump again.
- **Tag pushed but workflow did not run** — check the tag matches the
  ``tags: '*'`` trigger in ``release.yml`` and that the ``pypi``
  GitHub environment exists with no protection rules blocking the run.

