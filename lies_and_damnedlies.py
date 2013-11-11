# -*- coding: utf-8 -*-
"""

(Benchmarks)

Created on Wed Sep 04 14:55:02 2013

@author: caleb.hattingh
"""
from __future__ import absolute_import, division, print_function, unicode_literals
import timeit

unity_setup = '''import unity as u
def calc(mass, volume, time):
    for x in xrange(1000):
        y = mass * volume / time * x / 10000.
    return y
'''
unity_code = '''calc(10.0*u.kg, 5.0*u.m**3, 20.0*u.second)'''

pq_setup = '''import quantities as pq
def calc(mass, volume, time):
    for x in xrange(1000):
        y = mass * volume / time * x / 10000.
    return y
'''
pq_code = '''calc(10.0*pq.kg, 5.0*pq.m**3, 20.0*pq.second)'''

plain_setup = '''
def calc(mass, volume, time):
    for x in xrange(1000):
        y = mass * volume / time * x / 10000.
    return y
'''
plain_code = '''calc(10.0, 5.0, 20.0)'''

COUNT = 10

# Unity
print('{:15}: {:>8.4g} s'.format(
    'Unity', timeit.timeit(unity_code, unity_setup, number=COUNT)))
# Quantities
print('{:15}: {:>8.4g} s'.format(
    'Quantities', timeit.timeit(pq_code, pq_setup, number=COUNT)))
# Plain
print('{:15}: {:>8.4g} s'.format(
    'Pure Python', timeit.timeit(plain_code, plain_setup, number=COUNT)))
