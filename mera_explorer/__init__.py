#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The Met Eireann ReAnalysis explorer.

https://github.com/ThomasRieutord/mera-explorer
"""
import os

PACKAGE_DIRECTORY = os.path.split(__path__[0])[0]

NEURALLAM_VARIABLES = [  # Order matters
    "air_pressure_at_surface_level",
    "air_pressure_at_sea_level",
    "net_upward_longwave_flux_in_air",
    "net_upward_shortwave_flux_in_air",
    "relative_humidity_at_2_metres",
    "relative_humidity_at_30_metres",
    "air_temperature_at_2_metres",
    "air_temperature_at_30_metres",
    "air_temperature_at_500_hPa",
    "air_temperature_at_850_hPa",
    "eastward_wind_at_30_metres",
    "northward_wind_at_30_metres",
    "eastward_wind_at_850_hPa",
    "northward_wind_at_850_hPa",
    "atmosphere_mass_content_of_water_vapor",
    "geopotential_at_500_hPa",
    "geopotential_at_1000_hPa",
]

### Paths to MERA data on this machine
# [... mera-explorer]$ cat local/paths.txt
# MERAROOTDIR = "/data/trieutord/MERA/grib-all" # Parent directory of all MERA GRIB files
# MERACLIMDIR = "/data/trieutord/MERA/meraclim" # Directory where are stored climatology data (in particular the m05.grib)

with open(os.path.join(PACKAGE_DIRECTORY, "local", "paths.txt"), "r") as f:
    for l in f.readlines():
        if "MERAROOTDIR" in l:
            MERAROOTDIR = l.split('"')[1]
        if "MERACLIMDIR" in l:
            MERACLIMDIR = l.split('"')[1]

with open(os.path.join(PACKAGE_DIRECTORY, "pyproject.toml"), "r") as f:
    for l in f.readlines():
        if "version" in l:
            __version__ = l.split('"')[1]
            break

del f, l, os
