"""Shared pytest configuration for the misu test suite."""
import numpy as np
import pytest


@pytest.fixture(autouse=True, scope="session")
def _numpy_print_format():
    # Several `repr()` assertions expect '{:.3g}'-formatted ndarray output
    # (e.g. `'[1.45 2.91 4.36] kg'` in test_numpy_addition). Set globally
    # for the session so individual test files don't have to repeat it.
    np.set_printoptions(formatter=dict(all=lambda x: '{:.3g}'.format(x)))
