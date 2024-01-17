#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The Met Eireann ReAnalysis explorer.

Copy the GRIB files from one of the MERA drives.

Local transfer  --> This script is executed from the host where the drive is mounted
Remote transfer --> This script is executed from a server (localhost) connected to the host where the drive is mounted (remotehost)
"""

import os
import time
import datetime as dt
from mera_explorer import (
    gribs,
    utils,
    transfer
)
from mera_explorer.data import neurallam


# Identify the files to transfer
# ------------------------------
req_variables = neurallam.all_variables
valtimes = utils.datetime_arange("2017-09-15", "2017-11-15", "3h")
fsname = "reaext03"

req_gribnames = gribs.get_all_mera_gribnames(req_variables, valtimes, pathfromroot = False)
heregribnames = gribs.subset_present_gribnames(req_gribnames, fsname, exclude_bz2 = False)
print(f"Found {len(heregribnames)} GRIB files in {fsname} ({100*len(heregribnames)/len(req_gribnames)} % of all).")


# Make the transfer
# -----------------
### Local transfer
# trf = transfer.LocalTransfer(verbose = True)
# rem_rootdir = "/run/media/trieutord/reaext03"
# loc_rootdir = "/home/trieutord/Data/MERA/grib-sample-3GB"

### Remote transfer
remotehost = "realin15"
rusername = "trieutord"
trf = transfer.SSHTransfer(remotehost, rusername, verbose = True)
rem_rootdir = "/run/media/trieutord/reaext03"
loc_rootdir = "/data/trieutord/MERA/grib-sample-3GB"

src_gribnames = [
    os.path.join(rem_rootdir, gribs.expand_pathfromroot(fn)) for fn in heregribnames
]
trg_gribnames = [
    os.path.join(loc_rootdir, gribs.expand_pathfromroot(fn)) for fn in heregribnames
]
start_time = time.time()
trf.mget(src_gribnames, trg_gribnames)
end_time = time.time()
print(f"Total: {(end_time - start_time)/60} min elapsed ({(end_time-start_time)/len(heregribnames)} s/file)")

# Extract the bz2 files
# ---------------------
print("Uncompressing bz2...")
gribs.uncompress_all_bz2(loc_rootdir, verbose = True)

