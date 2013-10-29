# -*- coding: utf-8 -*-
"""
Created on Fri Sep 06 09:36:59 2013

@author: caleb.hattingh
"""
from __future__ import absolute_import, division, print_function, unicode_literals

from unity import *

COUNT = 100000

def testu():
    for x in xrange(COUNT):
        y = (100*kg/m**3) * (4000*m**3) / (210*g/cm**3 + x*kg/m**3)

def test():
    for x in xrange(COUNT):
        y = (100) * (4000) / (210 + x)


if __name__ == '__main__':
    test()
    testu()
