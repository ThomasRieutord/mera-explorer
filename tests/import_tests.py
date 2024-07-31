#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Multiple land-cover/land-use Maps Translation (MMT)

Program to test import of the package.
"""
import mera_explorer
from mera_explorer import gribs
from mera_explorer import transfer
from mera_explorer import forecasts

from mera_explorer import PACKAGE_DIRECTORY, MERAROOTDIR, MERACLIMDIR

print(f"Package {mera_explorer} successfully imported from {PACKAGE_DIRECTORY}")
print(f"GRIB files are expected to be in {MERAROOTDIR}")
print(f"Climatology file (m05.grib) is expected to be in {MERACLIMDIR}")
