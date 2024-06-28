#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The Met Eireann ReAnalysis explorer.

https://github.com/ThomasRieutord/mera-explorer
"""
import os

PACKAGE_DIRECTORY = os.path.split(__path__[0])[0]
MERAROOTDIR = "/data/trieutord/MERA/grib-all"
MERACLIMDIR = "/data/trieutord/MERA/meraclim"

with open(os.path.join(PACKAGE_DIRECTORY, "setup.py"), "r") as f:
    for l in f.readlines():
        if "version=" in l:
            __version__ = l.split('"')[1]
            break

del f, l, os
