"""The ``dimensions`` decorator implementation.

Kept in pure Python because it walks user-defined function signatures and
calls back into Python — a Rust port wouldn't make this faster, and the
Python implementation handles every edge case (defaults, *args, **kwargs)
that real callers throw at it.
"""
from __future__ import annotations

from misu._engine import Quantity


def make_dimensions_decorator(spec):
    """Returns a decorator that enforces unit categories on named arguments.

    Equivalent to::

        @dimensions(rho='Mass density', v='Velocity')
        def f(rho, v):
            ...

    Implementation lives here (not in Rust) so that the Rust ``dimensions``
    pyfunction can stay tiny and so that decorating user code does not pay
    the cost of crossing the FFI boundary on every call.
    """
    def check_types(func):
        def modified(*args, **kw):
            arg_names = func.__code__.co_varnames
            kw.update(zip(arg_names, args))
            for name, category in spec.items():
                param = kw[name]
                if not isinstance(param, Quantity):
                    raise AssertionError(
                        f'Parameter "{name}" must be an instance of class '
                        f'Quantity (and must be of unit type "{category}").'
                    )
                if param.unitCategory() != category:
                    raise AssertionError(
                        f'Parameter "{name}" must be unit type "{category}".'
                    )
            return func(**kw)
        modified.__name__ = func.__name__
        modified.__doc__ = func.__doc__
        return modified
    return check_types
