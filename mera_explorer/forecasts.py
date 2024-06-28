#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The Met Eireann ReAnalysis explorer

Tools to write forecasts.


Useful links
------------
CF Standard names
    http://cfconventions.org/Data/cf-standard-names/current/build/cf-standard-name-table.html

List of GRIB1 indicatorOfParameters
    https://codes.ecmwf.int/grib/format/grib1/parameter/2/

Operational forecasts:
    reaserve:/nfs/archive/prod/archive/Harmonie/UWCW_DINIeps/2024/06/17/12/mbr000/fc202406171200_0_accum_tp_sfc_0_geo_46.8264_344.593_639x730x2000m.grib2
    atos:/scratch/dujf/hm_home/sp24d1s1tRFAC_R0/archive/2023/06/20/00/mbr001/ICMSHHARM+0015

Archived VLFD:
    reaserve:/nfs/cvichec/nwpver/harmonie/IREPS/mbr000/2023/04/vfldIREPSmbr0002023042715.tar.gz

Archived VOBS:
    reaserve:/data/opver/nwpver/vobs/synop/vobs2018060422

Example of ML output forecast:
    [rootdir/]$INFERENCEID/$YYYY/$MM/$DD/$HH/$MEMBRE/$INFERENCEID$YYYY$MM$DD$HH+$LDT.grib
    

Notes
-----
Forecasts are stored the same directory structure as the operational forecast and
each GRIB file contains all variables for a single validity time.
"""
import os
import numpy as np
import datetime as dt
import climetlab as cml
import xarray as xr

from mera_explorer import utils, gribs, MERACLIMDIR, MERAROOTDIR, PACKAGE_DIRECTORY


DEFAULT_ROOTDIR = os.path.join(os.environ["SCRATCH"], "neural-lam-outputs")
DEFAULT_INFERENCEID = "aifc"
GRIB_TEMPLATE = "TEMPLATE17_2014062912+000.grib"


def get_path_from_times(
    basetime, leadtime, inferenceid=DEFAULT_INFERENCEID, rootdir=DEFAULT_ROOTDIR
) -> str:
    """Return the expected path for a given base time and lead time
    
    
    Parameters
    ----------
    basetime: dt.datetime or str
        Base time (when the forecast starts)
    
    leadtime: dt.timedelta or str
        Lead time (how far ahead from the base time)
    
    inferenceid: str
        Identificator of the inference run
    
    rootdir: str
        Root directory
    
    
    Example
    -------
    >>> get_path_from_times("2014-05-12", "30h")
    '/data/trieutord/scratch/neural-lam-outputs/aifc/2014/05/12/00/mbr000/aifc2014120500+030.grib'
    """
    basetime = utils.str_to_datetime(basetime)
    leadtime = utils.str_to_timedelta(leadtime)
    strldt = str(int(leadtime.total_seconds() // 3600)).zfill(3)
    return os.path.join(
        rootdir,
        inferenceid,
        *[
            str(_).zfill(2) for _ in [
                basetime.year,
                basetime.month,
                basetime.day,
                basetime.hour,
            ]
        ],
        "mbr000",
        inferenceid + basetime.strftime("%Y%d%m%H") + f"+{strldt}.grib",
    )

def get_all_paths_from_times(
    basetimes, leadtimes, inferenceid=DEFAULT_INFERENCEID, rootdir=DEFAULT_ROOTDIR
) -> list:
    paths = []
    for basetime in basetimes:
        for leadtime in leadtimes:
            paths.append(
                get_path_from_times(basetime, leadtime, inferenceid, rootdir)
            )
    
    return paths

def get_times_from_gribname(gribname) -> tuple:
    """Extract the time (validity time, base time, lead time) from the GRIB name.


    Example
    -------
    >>> get_time_from_gribname("aifc2014062912+030.grib")
    (datetime.datetime(2014, 6, 30, 18, 0), datetime.datetime(2014, 6, 29, 12, 0), datetime.timedelta(days=1, seconds=21600))
    """
    gribname = os.path.basename(gribname)
    if "+" not in gribname:
        raise ValueError(
            f"Unable to parse the time from the GRIB {gribname} as there is no '+' sign."
        )

    p = gribname.index("+")
    basetime = dt.datetime.strptime(gribname[p - 10 : p], "%Y%m%d%H")
    leadtime = dt.timedelta(hours=int(gribname[p + 1 : p + 4]))
    valtime = basetime + leadtime
    return valtime, basetime, leadtime


def write_in_grib(data, template, outgribname):
    cfnames = data.keys()
    _, _, leadtime = get_time_from_gribname(outgribname)
    ldt = leadtime.total_seconds() // 3600
    
    for i, (onevarfield, cfname) in enumerate(zip(template, cfnames)):
        with cml.new_grib_output(outgribname.replace(".grib", f".{cfname}.grib"), template=onevarfield, step = ldt) as output:
            output.write(data[cfname])

    griblist = " ".join([outgribname.replace(".grib", f".{cfname}.grib") for cfname in cfnames])
    cat_cmd = f"cat {griblist} > {outgribname}"
    rm_cmd = f"rm {griblist}"
    os.system(cat_cmd)
    os.system(rm_cmd)
    print(f"Written: {outgribname}")
    return outgribname

def create_analysis(basetime, cfnames, max_leadtime, inferenceid, step = dt.timedelta(hours=3)):
    basetime = utils.str_to_datetime(basetime)
    max_leadtime = utils.str_to_timedelta(max_leadtime)
    
    valtimes = []
    outgribnames = []
    for i_ldt in range(-1, max_leadtime // step + 1):
        leadtime = i_ldt * step
        valtimes.append(basetime + leadtime)
        outgribnames.append(
            get_path_from_times(basetime, leadtime, inferenceid)
        )
    
    for outgribname, val_t in zip(outgribnames, valtimes):
        os.makedirs(os.path.dirname(outgribname), exist_ok=True)
        for cfname in cfnames:
            gribname = os.path.join(
                MERAROOTDIR,
                gribs.get_mera_gribname_valtime(cfname, val_t, pathfromroot=True),
            )
            
            if not os.path.isfile(gribname):
                print(f"\t\tMISSING: {cfname} {gribname}")
                continue
        
            x = gribs.get_data(gribname, val_t)
            
            src = cml.load_source("file", gribname)
            t_idx = (val_t - gribs.get_date_from_gribname(gribname))//dt.timedelta(hours=3)
            template = src[t_idx]
            with cml.new_grib_output(outgribname.replace(".grib", f".{cfname}.grib"), template=template) as output:
                output.write(x)
    
        griblist = " ".join([outgribname.replace(".grib", f".{cfname}.grib") for cfname in cfnames])
        cat_cmd = f"\t cat {griblist} > {outgribname}"
        rm_cmd = f"\t rm {griblist}"
        os.system(cat_cmd)
        os.system(rm_cmd)
        # print(f"Written: {outgribname}")
    
    return outgribnames

def create_forcings(basetime, max_leadtime, inferenceid, step = dt.timedelta(hours=3)):
    toaswf_cfname = "toa_incoming_shortwave_flux"
    basetime = utils.str_to_datetime(basetime)
    max_leadtime = utils.str_to_timedelta(max_leadtime)
    
    valtimes = [basetime + i_ldt * step for i_ldt in range(-1, max_leadtime // step + 1)]
    
    outdir = os.path.dirname(get_path_from_times(basetime, "0h", inferenceid))
    forcings_file = os.path.join(outdir, "forcings" + basetime.strftime("%Y%m%d%H") + ".nc")
    
    # TOA files
    count = 0
    for val_t in valtimes:
        gribname = os.path.join(
            MERAROOTDIR,
            gribs.get_mera_gribname_valtime(
                toaswf_cfname, val_t, pathfromroot=True
            ),
        )
        if count == 0:
            toaswf = gribs.get_data(gribname, val_t)
        else:
            x_t = gribs.get_data(gribname, val_t)
            toaswf = np.dstack((toaswf, x_t))
        
        count += 1
    
    toaswf = np.swapaxes(toaswf, 0, 2)
    toaswf = np.swapaxes(toaswf, 1, 2)
    # print("\t\t", toaswf_cfname, toaswf.shape, toaswf.min(), toaswf.mean(), toaswf.max())
    
    
    # WRT files
    sfx = xr.open_dataset(
        os.path.join(MERACLIMDIR, "m05.grib"),
        engine="cfgrib",
        filter_by_keys={"typeOfLevel": "heightAboveGround"},
        backend_kwargs={
            "indexpath": os.path.join(gribs.index_path, "m05.grib.idx")
        },
    )
    lsm = sfx.lsm.to_numpy()
    # print("\t\tland_sea_mask", lsm.shape, lsm.min(), lsm.mean(), lsm.max())

    nx, ny = lsm.shape
    ds = xr.Dataset(
        {
            toaswf_cfname: (("t", "x", "y"), toaswf),
            "land_sea_mask":(("x", "y"), lsm),
        },
        coords={
            "x": range(nx),
            "y": range(ny),
            "t": valtimes,
        },
    )
    ds.to_netcdf(forcings_file)
    
    return forcings_file


def create_mera_analysis_and_forcings(startdate, enddate, max_leadtime = "54h", textract = "72h"):
    basetimes = utils.datetime_arange(startdate, enddate, textract)
    cfnames = gribs.read_variables_from_yaml(os.path.join(PACKAGE_DIRECTORY, "mera_explorer", "data", "neurallam.yaml"))
    for i_bt, basetime in enumerate(basetimes):
        create_analysis(basetime, cfnames, max_leadtime = "54h", inferenceid = "mera")
        forcings_file = create_forcings(basetime, max_leadtime = "54h", inferenceid = "mera")
        print(f"[{i_bt}/{len(basetimes)}] Basetime {basetime} written in {os.path.dirname(forcings_file)}")
