#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The Met Eireann ReAnalysis explorer.

Program for creating samples for Neural-LAM

USAGE -- example

python create_mera_sample.py --datadir /data/trieutord/MERA/ --outdir data/emcaufield/neural_LAM/neural-lam/data/mera_example_emca/samples --sdate 2015-01-02 --edate 2015-02-01 --tstep 3h --tlag 65h


Target tree of files
--------------------

meps_example
├── samples
│   ├── test
│   │   ├── nwp_2022090100_mbr000.npy
│   │   ├── nwp_2022090100_mbr001.npy
│   │   ├── nwp_2022090112_mbr000.npy
│   │   ├── nwp_2022090112_mbr001.npy
│   │   ├── nwp_toa_downwelling_shortwave_flux_2022090100.npy
│   │   ├── nwp_toa_downwelling_shortwave_flux_2022090112.npy
│   │   ├── wtr_2022090100.npy
│   │   └── wtr_2022090112.npy
│   ├── train
│   │   ├── nwp_2022040100_mbr000.npy
│   │   ├── nwp_2022040100_mbr001.npy
│   │   ├── nwp_2022040112_mbr000.npy
│   │   ├── nwp_2022040112_mbr001.npy
│   │   ├── nwp_toa_downwelling_shortwave_flux_2022040100.npy
│   │   ├── nwp_toa_downwelling_shortwave_flux_2022040112.npy
│   │   ├── wtr_2022040100.npy
│   │   └── wtr_2022040112.npy
│   └── val
│       ├── nwp_2022060500_mbr000.npy
│       ├── nwp_2022060500_mbr001.npy
│       ├── nwp_2022060512_mbr000.npy
│       ├── nwp_2022060512_mbr001.npy
│       ├── nwp_toa_downwelling_shortwave_flux_2022060500.npy
│       ├── nwp_toa_downwelling_shortwave_flux_2022060512.npy
│       ├── wtr_2022060500.npy
│       └── wtr_2022060512.npy
└── static
    ├── border_mask.npy
    ├── nwp_xy.npy
    └── surface_geopotential.npy

This program only creates the `samples` directory. For the `static` features,
see the program `create_static_features.py`


Shapes of target files
----------------------
On the MEPS example, the shapes are the following...
    nwp_*mbr*.npy   (65, 268, 238, 18)
    nwp_toa_*.npy   (65, 268, 238)
    wtr_*.npy       (268, 238)

...and indices:
    65 = time index (65-h lead time in MEPS)
    18 = variables index
    (268, 238) = geographical domain

For the variables index, here is the order:
    0    -> air_pressure_at_surface_level            (pres_0g)
    1    -> air_pressure_at_sea_level                (pres_0s)
    2    -> net_upward_longwave_flux_in_air          (nlwrs)
    3    -> net_upward_shortwave_flux_in_air         (nswrs)
    4    -> relative_humidity_at_2_metres            (r_2)
    5    -> relative_humidity_at_12_metres           (r_65)
    6    -> air_temperature_at_2_metres              (t_2)
    7    -> air_temperature_at_12_metres             (t_65)
    8    -> air_temperature_at_500_hPa               (t_500)
    9    -> air_temperature_at_850_hPa               (t_850)
    10   -> eastward_wind_at_12_metres               (u_65)
    11   -> northward_wind_at_12_metres              (v_65)
    12   -> eastward_wind_at_850_hPa                 (u_850)
    13   -> northward_wind_at_850_hPa                (v_850)
    14   -> atmosphere_mass_content_of_water_vapor   (wvint)
    15   -> z_height_above_ground                    (* UNUSED *)
    16   -> geopotential_at_500_hPa                  (z_500)
    17   -> geopotential_at_1000_hPa                 (z_1000)


From MEPS to MERA
-----------------
nwp_2022040100_mbr000: 65-h hourly forecast from member 0 starting from analysis at 2022-04-01 00Z.

nwp_2022040100_mbr000: 21 3-hourly analysis starting at 2022-04-01 00Z (member ignored).
 => in neurallam.WeatherDataset:
        subsample_step = 1
        control_only = True
"""


import os
import numpy as np
import datetime as dt
import xarray as xr
import matplotlib.pyplot as plt
import easydict
from pprint import pprint
from mera_explorer import (
    _repopath_,
    gribs,
    utils,
)
from mera_explorer.data import neurallam
import argparse

writefiles = True

# cfnames = neurallam.neurallam_variables
cfnames = [  # Order matters
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
    "atmosphere_mass_content_of_water_vapor",  # unused
    "geopotential_at_500_hPa",
    "geopotential_at_1000_hPa",
]
toaswf_cfname = "toa_incoming_shortwave_flux"

parser = argparse.ArgumentParser(prog="create_mera_sample.py")
parser.add_argument('--datadir', help="Path to MERA data directory")
parser.add_argument('--outdir', help="Output data directory")
parser.add_argument('--sdate', type=dt.datetime.fromisoformat, help="Start date in ISO format - YYYY-MM-DD")
parser.add_argument('--edate', type=dt.datetime.fromisoformat, help="End date in ISO format - YYYY-MM-DD")
parser.add_argument('--tstep', help="Time step for file creation", default="3h")
parser.add_argument('--tlag', help="Forecast time", default="65h")
args=parser.parse_args()

meraclimroot = args.datadir+"meraclim"
merarootdir = args.datadir+"grib-all"
npyrootdir = args.outdir


ss = lambda x: utils.subsample(x, 2)


start = args.sdate 
print(start)
anchortimes = utils.datetime_arange(
    start, args.edate - utils.str_to_timedelta("72h"), "72h"
)
anchorsplit = {
    "train": anchortimes[:4],
    "test": anchortimes[4:7],
    "val": anchortimes[7:],
}

for subset, anchortimes in anchorsplit.items():
    print(f"\n=== {subset.upper()} ===")
    gribnames = []
    npysavedir = os.path.join(npyrootdir, subset)
    os.makedirs(npysavedir, exist_ok=True)

    for i_anchor, anchor in enumerate(anchortimes):
        npyfilename = "nwp_" + anchor.strftime("%Y%m%d%H") + "_mbr000.npy"
        toafilename = (
            "nwp_toa_downwelling_shortwave_flux_" + anchor.strftime("%Y%m%d%H") + ".npy"
        )
        wtrfilename = "wtr_" + anchor.strftime("%Y%m%d%H") + ".npy"

        # NWP files
        # ---------
        X = []
        print(f"[{i_anchor + 1}/{anchortimes.size}]", anchor, npyfilename)
        valtimes = utils.datetime_arange(
            anchor, anchor + utils.str_to_timedelta(args.tlag), args.tstep
        )

        for cfname in cfnames:
            gribname = os.path.join(
                merarootdir,
                gribs.get_mera_gribname_valtime(cfname, anchor, pathfromroot=True),
            )
            if not os.path.isfile(gribname):
                print(f"\t\tMISSING: {cfname} {os.path.basename(gribname)}")
                continue

            x = ss(gribs.get_data(gribname, valtimes))
            print("\t\t", cfname, x.shape, x.min(), x.mean(), x.max())
            X.append(x)
            gribnames.append(gribname)

        if writefiles:
            np.save(os.path.join(npysavedir, npyfilename), np.stack(X, axis=-1))
            print(f"\tSaved: {os.path.join(npysavedir, npyfilename)}")

        # TOA files
        # ---------
        gribname = os.path.join(
            merarootdir,
            gribs.get_mera_gribname_valtime(toaswf_cfname, anchor, pathfromroot=True),
        )
        x = ss(gribs.get_data(gribname, valtimes))
        print("\t\t", toaswf_cfname, x.shape, x.min(), x.mean(), x.max())
        gribnames.append(gribname)

        if writefiles:
            np.save(os.path.join(npysavedir, toafilename), x)
            print(f"\tSaved: {os.path.join(npysavedir, toafilename)}")

        # WRT files
        # ---------
        sfx = xr.open_dataset(
            os.path.join(meraclimroot, "m05.grib"),
            engine="cfgrib",
            filter_by_keys={"typeOfLevel": "heightAboveGround"},
            backend_kwargs={
                "indexpath": os.path.join(gribs.index_path, "m05.grib.idx")
            },
        )
        x = ss(sfx.lsm.to_numpy())
        print("\t\tland_sea_mask", x.shape, x.min(), x.mean(), x.max())

        if writefiles:
            np.save(os.path.join(npysavedir, wtrfilename), x)
            print(f"\tSaved: {os.path.join(npysavedir, wtrfilename)}")

    print(f"\t{len(gribnames)} GRIB used:")
    pprint(gribnames)
