#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The Met Eireann ReAnalysis explorer.

Check if the requested variables are in the hard drives at Met Eireann HQ


How to proceed
--------------
  1. Edit the YAML file at `mera_explorer/data/mydata.yaml`
  2. Launch `python is_my_data_there.py`


Examples
--------
python is_my_data_there.py
    Check all the file systems for the variables in the file at `mera_explorer/data/mydata.yaml`

python is_my_data_there.py --fs=reaext03 --vars=neurallam.yaml
    Check for the variables in the file at `mera_explorer/data/neurallam.yaml` and only in the reaext03 file system
"""

import os
import argparse
from pprint import pprint
from mera_explorer import (
    gribs,
    _repopath_
)
from mera_explorer.data import my_data

# Argument parsing
# ----------------
parser = argparse.ArgumentParser(prog="is_my_data_there")
parser.add_argument("--fs", help="File system name (reaext0*, all, path to local directory)", default="all")
parser.add_argument("--vars", help="YAML file describing the set of atmospheric variables to check", default="mydata.yaml")
args = parser.parse_args()

### Set of variables
yaml_file = os.path.join(_repopath_, "mera_explorer", "data", args.vars)
assert os.path.isfile(yaml_file), f"File not found: {yaml_file}"


# Starting program
# ----------------
atm_variables = gribs.read_variables_from_yaml(yaml_file)

print(f"Looking for {len(atm_variables)} variables in {args.fs} file system")

merafilenames = gribs.list_mera_gribnames(args.fs)

iop_itl_lev_tri = [
    "_".join([str(d) for d in gribs.get_grib1id_from_cfname(cfname)])
    for cfname in atm_variables
]

missingvarnames = []
print("\nVAR.CODE \t VAR.NAME                                \t #FILES")
print("--------- \t ---------                                \t ---------")
for varcode, varname in zip(iop_itl_lev_tri, atm_variables):
    n_files_here = len([_ for _ in merafilenames if varcode in _])
    print(f"{varcode} \t {varname.ljust(40)} \t {n_files_here} files for this variable in this filesystem")
    
    if n_files_here == 0:
        missingvarnames.append(varname)

print(f"\n{len(missingvarnames)} are missing:")
pprint(missingvarnames)

gribdates = [gribs.get_date_from_gribname(gn) for gn in merafilenames]
gribs.count_dates_per_month(gribdates)

