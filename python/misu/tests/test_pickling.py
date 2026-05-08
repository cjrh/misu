import pickle

import numpy as np

from misu import kg, s


def test_pickle():
    var = 2.5 * kg / s
    pick = pickle.dumps(var)
    res = pickle.loads(pick)
    assert var==res

def test_pickle_np():
    var = np.array([2.5, 4]) * kg / s
    pick = pickle.dumps(var)
    res = pickle.loads(pick)
    assert (var[0]==res[0] and var[1]==res[1])
