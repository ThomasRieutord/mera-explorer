#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The Met Eireann ReAnalysis explorer.

Create static features for Neural-LAM training.


Tree of files to be written:

data
└── mera_example
    ├── samples
    └── static
        ├── surface_geopotential.npy
        ├── border_mask.npy
        └── nwp_xy.npy


NOTES
=====

Convert FA/LFI to GRIB
----------------------

The meraclim dir contains FA/LFI files that must be converted in GRIB beforehand.
The orography is stored in the monthly clim (m* files).
Here is the command to convert them (25 Jan. 2024):

[trieutord@REAServe2 meraclim]$ ll
total 2202284
-rw-r-----. 1 trieutord trieutord 445169664 Mar 26  2015 Const.Clim.sfx
-rw-rw-r--. 1 trieutord trieutord        50 Jan 22 17:12 excl.nam
-rw-r-----. 1 trieutord trieutord  40132608 Mar 26  2015 m01
-rw-r-----. 1 trieutord trieutord  40132608 Mar 26  2015 m02
-rw-r-----. 1 trieutord trieutord  40132608 Mar 26  2015 m03
-rw-r-----. 1 trieutord trieutord  40132608 Mar 26  2015 m04
-rw-r-----. 1 trieutord trieutord  40132608 Mar 26  2015 m05
-rw-r-----. 1 trieutord trieutord  40132608 Mar 26  2015 m06
-rw-r-----. 1 trieutord trieutord  40132608 Mar 26  2015 m07
-rw-r-----. 1 trieutord trieutord  40132608 Mar 26  2015 m08
-rw-r-----. 1 trieutord trieutord  40132608 Mar 26  2015 m09
-rw-r-----. 1 trieutord trieutord  40132608 Apr 12  2015 m10
-rw-r-----. 1 trieutord trieutord  40132608 Apr 12  2015 m11
-rw-r-----. 1 trieutord trieutord  40132608 Apr 21  2015 m12
-rw-r-----. 1 trieutord trieutord 421552128 Mar 26  2015 PGD.lfi
-rw-r-----. 1 trieutord trieutord 426418176 Mar 26  2015 PGD_prel.fa
-rw-r-----. 1 trieutord trieutord 421699584 Mar 26  2015 PGD_prel.lfi
[trieutord@REAServe2 meraclim]$ module load gl
[trieutord@REAServe2 meraclim]$ gl -p m05 -o m05.grib -igd
"""

import os
import yaml
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import easydict
from pprint import pprint
from pyproj import Transformer
from mera_explorer import _repopath_, utils
import argparse


parser = argparse.ArgumentParser(
    prog="create_static_features.py",
    description="Create static features for Neural-LAM",
    epilog="Example: python create_static_features.py --indirclim /data/trieutord/MERA/meraclim --outdirmllam /data/emcaufield/neural_LAM/neural-lam/data/mera_example_emca2",
)
parser.add_argument("--indirclim", help="Path to MERA climatology directory")
parser.add_argument(
    "--outdirmllam",
    help="Path to the data sample for Neural-LAM (from create_mera_sample.py)",
)
parser.add_argument(
    "--writefiles",
    help="Files will actually be written if present (they will not if the flag is not present)",
    action="store_true",
)
parser.add_argument("--subsample", help="Subsampling factor (1=no subsampling, 2=every other point...)", default=1)
args = parser.parse_args()

writefiles = args.writefiles
meraclimroot = args.indirclim
mllamdataroot = args.outdirmllam

dtype = np.float32
ss = lambda x: utils.subsample(x, args.subsample)
os.makedirs(os.path.join(mllamdataroot, "static"), exist_ok=True)

sfx = xr.open_dataset(
    os.path.join(meraclimroot, "m05.grib"),
    engine="cfgrib",
    filter_by_keys={"typeOfLevel": "heightAboveGround"},
)


# Create the orography file: surface_geopotential
# --------------------------
orofile = os.path.join(mllamdataroot, "static", "surface_geopotential.npy")
print(f"Orography file to be written in {orofile}")


z = ss(sfx.z.to_numpy().astype(dtype))
print(f"    z.shape={z.shape} {z.dtype}")

if writefiles:
    np.save(orofile, z)
    print(f"    Saved: {orofile}")


# Create the geometry file: nwp_xy
# -------------------------
xyfile = os.path.join(mllamdataroot, "static", "nwp_xy.npy")
print(f"Geometry file to be written in {xyfile}")

meregeomfile = os.path.join(
    _repopath_, "mera_explorer", "data", "mera-grid-geometry.yaml"
)
assert os.path.isfile(
    meregeomfile
), f"File with MERA geometry is missing at {meregeomfile}"

with open(meregeomfile, "r") as f:
    geom = yaml.safe_load(f)

g = easydict.EasyDict(geom["geometry"])
meracrs = f"+proj=lcc +lat_0={g.projlat} +lon_0={g.projlon} +lat_1={g.projlon} +lat_2={g.projlat2} +x_0={g.polon} +y_0={g.polat} +datum=WGS84 +units=m +no_defs"

# pp = easydict.EasyDict(constants.lambert_proj_params)
# meracrs = f"+proj=lcc +lat_0={pp.lat_0} +lon_0={pp.lon_0} +lat_1={pp.lat_1} +lat_2={pp.lat_2} +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"

crstrans = Transformer.from_crs("EPSG:4326", meracrs, always_xy=True)

x, y = crstrans.transform(
    sfx.longitude.to_numpy().astype(dtype), sfx.latitude.to_numpy().astype(dtype)
)

xy = ss(np.array([x, y], dtype=dtype))


print(f"    xy.shape={xy.shape} {xy.dtype}")

if writefiles:
    np.save(xyfile, xy)
    print(f"    Saved: {xyfile}")


# Create the border file: border_mask
# -----------------------
borfile = os.path.join(mllamdataroot, "static", "border_mask.npy")
print(f"Border file to be written in {borfile}")

xy = np.load(xyfile)
border = np.ones_like(xy[0])
border[10:-10, 10:-10] = 0
print(f"    border.shape={border.shape} {border.dtype}")

if writefiles:
    np.save(borfile, border)
    print(f"    Saved: {borfile}")


# Create the land/sea mask: wrt_mask
# ------------------------
wrtfile = os.path.join(mllamdataroot, "static", "wrt_mask.npy")
print(f"Land/sea mask file to be written in {wrtfile}")

lsm = ss(sfx.lsm.to_numpy().astype(dtype))
print(f"    lsm.shape={lsm.shape} {lsm.dtype}")

if writefiles:
    np.save(wrtfile, 1 - lsm)
    print(f"    Saved: {wrtfile}")


# Create the constants file: constants.yaml
# -------------------------
cstfile = os.path.join(mllamdataroot, "static", "constants.yaml")
constants = {
    "DATASETNAME": os.path.basename(mllamdataroot),
    "N_TIMESTEPS_PER_FILE": 21,
    "GRID_SHAPE": list(lsm.shape),
    "GRID_LIMITS": np.array([x.min(), x.max(), y.min(), y.max()]).tolist(),
    "LAMBERT_PROJ_PARAMS": {
        "a": 6367470,
        "b": 6367470,
        "lat_0": g.projlat,
        "lat_1": g.projlat,
        "lat_2": g.projlat2,
        "lon_0": g.projlon,
        "proj": "lcc",
    },
}
pprint(constants)
if writefiles:
    with open(cstfile, "w") as yf:
        yaml.dump(constants, yf)

with open(cstfile, "r") as yf:
    cst = yaml.safe_load(yf)
