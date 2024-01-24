#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The Met Eireann ReAnalysis explorer.

Copy the GRIB files from one of the MERA drives.

Local transfer  --> This script is executed from the host where the drive is mounted
Remote transfer --> This script is executed from a server (localhost) connected to the host where the drive is mounted (remotehost)
"""

import os
import time
import argparse
import numpy as np
import datetime as dt
from mera_explorer import (
    _repopath_,
    gribs,
    utils,
    transfer
)
from mera_explorer.data import neurallam

# Argument parsing
# ----------------
parser = argparse.ArgumentParser(prog="copy_from_reaext")
parser.add_argument("--type", help="Type of transfer (ssh, ftp, local)", default="ssh")
parser.add_argument("--fs", help="File system name (reaext0*, all)", default="all")
parser.add_argument("--vars", help="YAML file describing the set of atmospheric variables to check", default="mydata.yaml")
parser.add_argument("--lrootdir", help="Root directory on the local host (where the files are put)")
parser.add_argument("--ruser", help="User name on the remote host", default="trieutord")
parser.add_argument("--rdates", help="Range of validity dates to transfer (ex: 1991-01_2001-04 transfers all GRIB from Jan. 1991 to Apr. 2001)", default="1981-01_2016-12")
parser.add_argument('--verbose', help="Trigger verbose mode", action='store_true')
args = parser.parse_args()

### File system
if args.fs == "all":
    fstxt = os.path.join(_repopath_, "filesystems", "allmerafiles.txt")
else:
    fstxt = os.path.join(_repopath_, "filesystems", f"merafiles_{args.fs}.txt")

assert os.path.isfile(fstxt), f"Incorrect path to the file system TXT export: {fstxt}"

### Set of variables
yaml_file = os.path.join(_repopath_, "mera_explorer", "data", args.vars)
assert os.path.isfile(yaml_file), f"File not found: {yaml_file}"

fsname = args.fs
type_of_tranfer = args.type.lower()
loc_rootdir = args.lrootdir
rusername = args.ruser
verbose = args.verbose


# Identify the files to transfer
# ------------------------------
remotehost, rem_rootdir = gribs.get_filesystem_host_and_root(fsname)
req_variables = gribs.read_variables_from_yaml(yaml_file)
start = args.rdates.split("_")[0] + "-01"
stop = args.rdates.split("_")[-1] + "-28"
valtimes = utils.datetime_arange(start, stop, "10d")

req_gribnames = gribs.get_all_mera_gribnames(req_variables, valtimes, pathfromroot = False)
heregribnames = gribs.subset_present_gribnames(req_gribnames, fsname, exclude_bz2 = False)
print(f"Found {len(heregribnames)} GRIB files in {fsname} ({100*len(heregribnames)/len(req_gribnames)} % of all).")

if remotehost == "hpc-login":
    excluded = ",".join(
        [
            f"*YEAR_{y}*"
            for y in range(1981, 2017)
            if y not in np.unique([d.year for d in valtimes])
        ] + [
        "*_FC3*"
        ]
    )
    print(f"\n    rsync -avz --exclude={{{excluded}}} {rusername}@{remotehost}:{rem_rootdir}/mera/ {loc_rootdir}/mera/")
    exit(f"\nTransfer from/to {remotehost} do not work for the moment. Here is an example of rsync command that could be useful")

if type_of_tranfer == "local":
    trf = transfer.LocalTransfer(verbose = verbose)
elif type_of_tranfer == "ssh":
    trf = transfer.SSHTransfer(remotehost, rusername, verbose = verbose)
elif type_of_tranfer == "ftp":
    trf = transfer.FTPTransfer(remotehost, rusername, verbose = verbose)
else:
    raise ValueError(f"Unsupported type of tranfer: {type_of_tranfer}")

src_gribnames = [
    os.path.join(rem_rootdir, gribs.expand_pathfromroot(fn)) for fn in heregribnames
]
trg_gribnames = [
    os.path.join(loc_rootdir, gribs.expand_pathfromroot(fn)) for fn in heregribnames
]

print(f"Starting transfer from {remotehost}:{rem_rootdir} to {loc_rootdir}")
start_time = time.time()

trf.mget(src_gribnames, trg_gribnames)

end_time = time.time()
print(f"Total: {(end_time - start_time)/60} min elapsed ({(end_time-start_time)/len(heregribnames)} s/file)")


# Extract the bz2 files
# ---------------------
print("Uncompressing bz2...")
gribs.uncompress_all_bz2(loc_rootdir, verbose = True)

