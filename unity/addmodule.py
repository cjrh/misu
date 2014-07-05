# -*- coding: utf-8 -*-
"""
Created on Thu Mar  6 23:36:47 2014

@author: calebhattingh
"""

import os
import sys

def addpath(path=None):
    if path == None:
        new_syspath = os.path.join( os.path.dirname( __file__ ), '..' )
    else:
        new_syspath = os.path.join( os.path.dirname( __file__ ), path)
    sys.path.append(new_syspath)