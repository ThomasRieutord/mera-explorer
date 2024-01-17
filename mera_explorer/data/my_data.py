#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The Met Eireann ReAnalysis explorer.

Alternative way to create a set of variables to check.


How to proceed
--------------
  1. Edit the list of variables given in `all_variables`. Please use CF Standard names (see useful links).
    Grouping of vertical levels can be made thanks to the `gribs.add_vlevel_to_fieldnames` function.
    To display the help of this function in a terminal: `python -c "from mera_explorer import gribs; help(gribs.add_vlevel_to_fieldnames)"`

  2. Check that the list of variables is correct by executing the program `python data/my_data.py

  3. Export it into a YAML file following the given commands


Useful links
------------
CF Standard names
    http://cfconventions.org/Data/cf-standard-names/current/build/cf-standard-name-table.html
"""

from mera_explorer import gribs


all_variables = [
    "air_pressure_at_surface_level",
    "air_pressure_at_sea_level",
    "precipitation_amount",
] + gribs.add_vlevel_to_fieldnames(
    ["relative_humidity", "air_temperature"],
    [2, 100],    # In MEPS, the first level is at 65 m. We take 60 instead.
    "metres"
) + gribs.add_vlevel_to_fieldnames(
    ["eastward_wind", "northward_wind"],
    [10],    # In MEPS, the first level is at 65 m. We take 60 instead.
    "metres"
) + gribs.add_vlevel_to_fieldnames(
    ["air_temperature", "upward_air_velocity"],
    [700],
    "hPa"
) + gribs.add_vlevel_to_fieldnames(
    ["geopotential", "eastward_wind", "northward_wind", "air_temperature"],
    [1000, 850, 500],
    "hPa"
)


if __name__ == "__main__":
    from pprint import pprint
    print(f"{len(all_variables)} atmospheric variables:")
    pprint(all_variables)
    print("\nYAML exports: gribs.write_variables_to_yaml(all_variables, 'mydata.yaml')")
