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
import warnings

from mera_explorer import utils, gribs, MERACLIMDIR, MERAROOTDIR, PACKAGE_DIRECTORY


DEFAULT_ROOTDIR = os.path.join(os.environ["SCRATCH"], "neural-lam-outputs")
DEFAULT_INFERENCEID = "aifc"


def get_path_from_times(
    basetime, leadtime, inferenceid=DEFAULT_INFERENCEID
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
        DEFAULT_ROOTDIR,
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
        inferenceid + basetime.strftime("%Y%m%d%H") + f"+{strldt}.grib",
    )

def get_all_paths_from_times(
    basetimes, leadtimes, inferenceid=DEFAULT_INFERENCEID
) -> list:
    paths = []
    for basetime in basetimes:
        for leadtime in leadtimes:
            paths.append(
                get_path_from_times(basetime, leadtime, inferenceid)
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


def write_in_grib(data, template_file, outgribname):
    template = cml.load_source("file", template_file)
    cfnames = data.keys()
    _, _, leadtime = get_times_from_gribname(outgribname)
    ldt = leadtime.total_seconds() // 3600
    
    for i, (onevarfield, cfname) in enumerate(zip(template, cfnames)):
        with cml.new_grib_output(outgribname.replace(".grib", f".{cfname}.grib"), template=onevarfield, step = ldt) as output:
            output.write(data[cfname])

    griblist = " ".join([outgribname.replace(".grib", f".{cfname}.grib") for cfname in cfnames])
    cat_cmd = f"cat {griblist} > {outgribname}"
    rm_cmd = f"rm {griblist}"
    os.system(cat_cmd)
    os.system(rm_cmd)
    # print(f"Written: {outgribname}")
    return outgribname

def concatenate_states(states):
    nt = len(states)
    nv = len(states[0].keys())
    key = list(states[0].keys())[0]
    nx, ny = states[0][key].shape
    concat_states = np.zeros((nt, nx*ny, nv))
    for i_t, state in enumerate(states):    # len(states) = nt
        for i_v, key in enumerate(state.keys()):    # len(state.keys) = nv
            concat_states[i_t, :, i_v] = state[key].ravel() # (nx, ny)
        
    
    return concat_states # (nt, nx*ny, nv)

def separate_states(state, cfnames, gridshape):
    """Reverse operation to `concatenate_states`"""
    nt, n_grid, nv = state.shape
    assert nv == len(cfnames), "The list of variables does not match the number of dimensions"
    assert n_grid == gridshape[0]*gridshape[1], "Unable to reshape {n_grid} elements in {gridshape}"
    
    return [
        {
            cfnames[iv]:state[it,:,iv].reshape(gridshape)
            for iv in range(nv)
        }
        for it in range(nt)
    ]
    
def create_analysis(basetime, cfnames, max_leadtime, inferenceid, step = dt.timedelta(hours=3)):
    basetime = utils.str_to_datetime(basetime)
    max_leadtime = utils.str_to_timedelta(max_leadtime)
    step = utils.str_to_timedelta(step)
    
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
    step = utils.str_to_timedelta(step)
    
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
    
    
    # WRT files
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        # SerializationWarning: Unable to decode time axis into full numpy.datetime64 objects, continuing using cftime.datetime objects instead, reason: dates out of range
        sfx = xr.open_dataset(
            os.path.join(MERACLIMDIR, "m05.grib"),
            engine="cfgrib",
            filter_by_keys={"typeOfLevel": "heightAboveGround"},
            backend_kwargs={
                "indexpath": os.path.join(gribs.INDEX_PATH, "m05.grib.idx")
            },
        )
    
    lsm = sfx.lsm.to_numpy()
    # print("\t\tland_sea_mask", lsm.shape, lsm.min(), lsm.mean(), lsm.max())

    nt, nx, ny = toaswf.shape
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

def create_mera_analysis_and_forcings(startdate, enddate, max_leadtime = "54h", textract = "72h", step = "3h"):
    basetimes = utils.datetime_arange(startdate, enddate, textract)
    max_leadtime = utils.str_to_timedelta(max_leadtime)
    step = utils.str_to_timedelta(step)
    print(f"Writing {len(basetimes) * (max_leadtime//step + 3)} files from MERA in {DEFAULT_ROOTDIR}")
    
    cfnames = gribs.read_variables_from_yaml(os.path.join(PACKAGE_DIRECTORY, "mera_explorer", "data", "neurallam.yaml"))
    for i_bt, basetime in enumerate(basetimes):
        create_analysis(basetime, cfnames, max_leadtime = max_leadtime, inferenceid = "mera", step = step)
        forcings_file = create_forcings(basetime, max_leadtime = max_leadtime, inferenceid = "mera", step = step)
        print(f"[{i_bt}/{len(basetimes)}] Basetime {basetime} written in {os.path.dirname(forcings_file)}")

def get_datetime_forcing(datetimes, n_grid = None):
    start_of_year = dt.datetime(datetimes[0].year, 1, 1)
    seconds_into_year = np.array([(_ - start_of_year).total_seconds() for _ in datetimes])
    year_angle = (seconds_into_year * 2 * np.pi) / (365 * 24 * 3600) 
    hours_into_day = np.array([_.hour for _ in datetimes])
    hour_angle = (hours_into_day * 2 * np.pi) / 24
    datetime_forcing = np.stack(
        [
            np.sin(hour_angle),
            np.cos(hour_angle),
            np.sin(year_angle),
            np.cos(year_angle),
        ]
    )
    if n_grid is not None:
        nf, nt = datetime_forcing.shape
        datetime_forcing = np.broadcast_to(datetime_forcing, (n_grid, nf, nt)) # (n_grid, nf, nt)
        datetime_forcing = np.moveaxis(datetime_forcing, (0,1,2), (1,2,0)) # (nt, n_grid, nf)
    
    return datetime_forcing

def get_analysis(basetime, concat = True):
    prev_state_file = get_path_from_times(basetime, "-3h", "mera")
    curr_state_file = get_path_from_times(basetime, "0h", "mera")
    prev_state = gribs.read_multimessage_grib(prev_state_file)
    curr_state = gribs.read_multimessage_grib(curr_state_file)
    
    if concat:
        return concatenate_states([curr_state, prev_state])
    else:
        return curr_state, prev_state

def get_forcings(basetime):
    indir = os.path.dirname(get_path_from_times(basetime, "0h", "mera"))
    forcings_file = os.path.join(indir, "forcings" + basetime.strftime("%Y%m%d%H") + ".nc")
    forcing_data = xr.open_dataset(forcings_file)
    
    flux = forcing_data.toa_incoming_shortwave_flux.values
    nt, nx, ny = flux.shape
    flux = flux.reshape(nt, nx*ny, 1)
    
    datetime_forcing = get_datetime_forcing(
        [utils.datetime_from_npdatetime(_) for _ in forcing_data.t.values],
        n_grid = nx*ny
    )
    forcing_features = np.concatenate([flux, datetime_forcing], axis = -1) # (nt, n_grid, 5)
    forcing_windowed = np.concatenate(
        [
            forcing_features[:-2],
            forcing_features[1:-1],
            forcing_features[2:],
        ],
        axis = -1
    ) # (nt - 2, n_grid, 15)
    
    lsm = forcing_data.land_sea_mask.values
    lsm = np.broadcast_to(lsm.ravel(), (nt-2, nx*ny)).reshape((nt-2, nx*ny, 1)) # (nt - 2, n_grid, 1)
    
    forcing = np.concatenate([forcing_windowed, lsm], axis = -1)
    return forcing # (nt - 2, n_grid, 16)

def get_borders(basetime, max_leadtime, step = dt.timedelta(hours=3), concat = True):
    step = utils.str_to_timedelta(step)
    max_leadtime = utils.str_to_timedelta(max_leadtime)
    states = []
    for i_ldt in range(1, max_leadtime // step + 1):
        leadtime = i_ldt * step
        gribname = get_path_from_times(basetime, leadtime, "mera")
        state = gribs.read_multimessage_grib(gribname)
        states.append(state)
    
    if concat:
        return concatenate_states(states)
    else:
        return states

def forecast_from_analysis_and_forcings(startdate, enddate, forecaster, max_leadtime = "54h", textract = "72h", step = "3h"):
    step = utils.str_to_timedelta(step)
    basetimes = utils.datetime_arange(startdate, enddate, textract)
    for i_bt, basetime in enumerate(basetimes):
        analysis = get_analysis(basetime)
        forcings = get_forcings(basetime)
        borders = get_borders(basetime, max_leadtime)
        forecast = forecaster.forecast(analysis, forcings, borders)
        forecast_files = write_forecast(forecast, basetime, inferenceid=forecaster.shortname, step=step)
        print(f"[{i_bt}/{len(basetimes)}] Forecast from {forecaster.shortname} at basetime {basetime} written in {os.path.dirname(forecast_files[0])}")

def write_forecast(forecast, basetime, inferenceid, variables_to_write = "all", step = "3h"):
    step = utils.str_to_timedelta(step)
    grib_template = get_path_from_times(basetime, "0h", "mera")
    data_template = gribs.read_multimessage_grib(grib_template)
    cfnames = list(data_template.keys())
    gridshape = data_template[cfnames[0]].shape
    states = separate_states(forecast, cfnames, gridshape)
    if isinstance(variables_to_write, list):
        assert len(set(variables_to_write) & set(cfnames)) > 0, "The varibles to write are not all present in the forecast variables"
        states = [
            {k:state[k] for k in variables_to_write}
            for state in states
        ]
    
    forecast_files = []
    for i_ldt in range(len(states)):
        leadtime = step * (i_ldt +1)
        outgribname = get_path_from_times(basetime, leadtime, inferenceid)
        os.makedirs(os.path.dirname(outgribname), exist_ok=True)
        write_in_grib(states[i_ldt], grib_template, outgribname)
        forecast_files.append(outgribname)
        
    return forecast_files
