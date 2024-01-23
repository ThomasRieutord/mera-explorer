#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The Met Eireann ReAnalysis explorer.

Copy the GRIB files from one of the MERA drives.

Local transfer  --> This script is executed from the host where the drive is mounted
Remote transfer --> This script is executed from a server (localhost) connected to the host where the drive is mounted (remotehost)
"""

import os
import time
import numpy as np
import datetime as dt
from mera_explorer import (
    gribs,
    utils,
    transfer
)
from mera_explorer.data import neurallam


# Identify the files to transfer
# ------------------------------
req_variables = ["air_temperature_at_500_hPa", "air_temperature_at_850_hPa"]#neurallam.all_variables
valtimes = utils.datetime_arange("2016-09-15", "2016-11-15", "3h")
fsname = "ecfsdui"
loc_rootdir = "/data/trieutord/MERA/grib-sample-3GB"

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
remotehost, rem_rootdir = gribs.get_filesystem_host_and_root(fsname)
if remotehost == "hpc-login":
    rusername = "dutr"
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
else:
    rusername = "trieutord"
    trf = transfer.SSHTransfer(remotehost, rusername, verbose = True)

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

