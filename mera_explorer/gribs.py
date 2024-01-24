#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The Met Eireann ReAnalysis explorer

GRIB utilities.


Useful links
------------
MERA home page
    https://www.met.ie/climate/available-data/mera

CF Standard names
    http://cfconventions.org/Data/cf-standard-names/current/build/cf-standard-name-table.html

List of GRIB1 indicatorOfParameters
    https://codes.ecmwf.int/grib/format/grib1/parameter/2/
    

References
----------
[TN65]  Eoin Whelan, John Hanley, Emily Gleeson, 'The MÉRA Data Archive'
        Met Éireann Technical Note, 65, 2017-08-04
        URI: http://hdl.handle.net/2262/81711

"""

import os
import bz2
import yaml
import shutil
import numpy as np
import datetime as dt
from mera_explorer import utils, _repopath_

# DATA
# ====

cfname_to_iop = {
    "air_pressure":1,
    "geopotential":6,
    "geopotential_height":7,
    "air_temperature":11,
    "virtual_temperature":12,
    "air_potential_temperature":13,
    "wet_bulb_potential_temperature":14,
    "maximum_temperature":15,   #! Not in CF standard names
    "minimum_temperature":16,   #! Not in CF standard names
    "dew_point_temperature":17,
    "visibility_in_air":20,
    "wind_from_direction":31,
    "wind_speed":32,
    "eastward_wind":33,
    "northward_wind":34,
    "upward_air_velocity": 40,
    "atmosphere_absolute_vorticity":41,
    "atmosphere_relative_vorticity":43,
    "divergence_of_wind":44,
    "specific_humidity":51,
    "relative_humidity":52,
    "atmosphere_mass_content_of_water_vapor":54,    # = precipitable water
    "atmosphere_cloud_ice_content":58,
    "precipitation_flux":59,
    "thunderstorm_probability":60,
    "precipitation_amount":61,
    "large_scale_precipitation_amount":62,
    "convective_precipitation_amount":63,
    "surface_snow_amount":65,   # = water equivalent of snow depth
    "surface_snow_thickness":66,
    "ocean_mixed_layer_thickness":67,   #! Ambiguous GRIB code. May be atmosphere mixing layer thickness
    "cloud_area_fraction":71,
    "convective_cloud_area_fraction":72,
    "low_type_cloud_area_fraction":73,
    "medium_type_cloud_area_fraction":74,
    "high_type_cloud_area_fraction":75,
    "atmosphere_mass_content_of_cloud_condensed_water":76,   # = cloud water
    "land_binary_mask":81,  # 1=land, 0=sea
    "surface_roughness_length":83,
    "surface_albedo":84,
    "vegetation_area_fraction":87,
    "surface_net_upward_shortwave_flux":111,
    "surface_net_upward_longwave_flux":112,
    "toa_net_upward_shortwave_flux":113,
    "toa_outgoing_longwave_flux":114,
    "net_upward_longwave_flux_in_air":115,
    "net_upward_shortwave_flux_in_air":116,
    "surface_downwelling_shortwave_flux_in_air":117,
    "surface_upward_latent_heat_flux":121,
    "surface_upward_sensible_heat_flux":122,
    # Specific to MERA (see Tech. Note no 65)
    "x_wind_gust":162,
    "y_wind_gust":163,
}

cfname_to_default_grib1id = {
    # Taken from [TN65]
    #
    # CF Standard name                                  (IOP, ITL, LEV, TRI)
    "air_pressure":                                     (1, 105, 0, 0),
    "geopotential":                                     (6, 105, 0, 0),
    "geopotential_height":                              (7, 100, 850, 0),
    "air_temperature":                                  (11, 105, 2, 0),
    "virtual_temperature":                              (12, 105, 2, 0),
    "air_potential_temperature":                        (13, 105, 2, 0),
    "wet_bulb_potential_temperature":                   (14, 105, 2, 0),
    "maximum_temperature":                              (15, 105, 2, 2),    #! Not in CF standard names
    "minimum_temperature":                              (16, 105, 2, 2),    #! Not in CF standard names
    "dew_point_temperature":                            (17, 105, 0, 0),
    "visibility_in_air":                                (20, 105, 0, 0),
    "wind_from_direction":                              (31, 105, 10, 0),
    "wind_speed":                                       (32, 105, 10, 0),
    "eastward_wind":                                    (33, 105, 10, 0),
    "northward_wind":                                   (34, 105, 10, 0),
    "upward_air_velocity":                              (40, 100, 850, 0),
    "atmosphere_absolute_vorticity":                    (41, 100, 850, 0),
    "atmosphere_relative_vorticity":                    (43, 100, 850, 0),
    "divergence_of_wind":                               (44, 100, 850, 0),
    "specific_humidity":                                (51, 105, 2, 0),
    "relative_humidity":                                (52, 105, 2, 0),
    "atmosphere_mass_content_of_water_vapor":           (54, 200, 0, 0),    # = precipitable water
    "atmosphere_cloud_ice_content":                     (54, 200, 0, 0),
    "precipitation_amount":                             (61, 105, 0, 4),
    "surface_snow_amount":                              (65, 105, 0, 4),    # = water equivalent of snow depth
    "ocean_mixed_layer_thickness":                      (67, 105, 0, 0),    #! Ambiguous GRIB code. May be atmosphere mixing layer thickness
    "cloud_area_fraction":                              (71, 105, 0, 0),
    "low_type_cloud_area_fraction":                     (73, 105, 0, 0),
    "medium_type_cloud_area_fraction":                  (74, 105, 0, 0),
    "high_type_cloud_area_fraction":                    (74, 105, 0, 0),
    "atmosphere_mass_content_of_cloud_condensed_water": (76, 200, 0, 0),    # = cloud water
    "land_binary_mask":                                 (81, 105, 0, 0),    # 1=land, 0=sea
    "surface_roughness_length":                         (83, 105, 0, 0),
    "surface_albedo":                                   (84, 105, 0, 0),
    "vegetation_area_fraction":                         (87, 105, 0, 0),
    "surface_net_upward_shortwave_flux":                (111, 105, 0, 4),
    "surface_net_upward_longwave_flux":                 (112, 105, 0, 4),
    "toa_net_upward_shortwave_flux":                    (113, 8, 0, 4),
    "toa_outgoing_longwave_flux":                       (114, 8, 0, 4),
    "net_upward_longwave_flux_in_air":                  (115, 105, 0, 4),
    "net_upward_shortwave_flux_in_air":                 (116, 105, 0, 4),
    "surface_downwelling_shortwave_flux_in_air":        (117, 105, 0, 4),
    "surface_upward_sensible_heat_flux":                (122, 105, 0, 4),
    # Specific to MERA (see Tech. Note no 65)
    "x_wind_gust":                                      (162,105, 10, 2),
    "y_wind_gust":                                      (163,105, 10, 2),
}

unit_to_itl = {
    "hPa":100,
    "metres":105,
    "kelvin":20,
    # 8: Nominal top of atmosphere
    # 103: Specified altitude above mean sea level
    # 200: Entire atmosphere
}


# FUNCTIONS
# =========

def add_vlevel_to_fieldnames(lfn, lvlvl, vlvl_unit = "hPa"):
    """Add the appropriate suffix the field name to precise the vertical level
    according the CF conventions.
    
    
    Parameters
    ----------
    lfn: array-like
        List of file names
    
    lvlvl: array-like
        List of vertical levels
    
    vlvl_unit: str
        Vertical levels unit
    
    
    Returns
    -------
    lfnv: list
        List of field names with vertical level
    
    
    Examples
    --------
    >>> add_vlevel_to_fieldnames(["air_temperature", "geopotential_height"], [500, 850])
    >>> ["air_temperature_at_500_hPa", "air_temperature_at_850_hPa", "geopotential_height_at_500_hPa", "geopotential_height_at_850_hPa"]
    
    >>> add_vlevel_to_fieldnames(["air_temperature", "wind_speed"], [10], "metres")
    >>> ["air_temperature_at_10_metres", "wind_speed_at_10_metres"]
    """
    lfnv = []
    for fd in lfn:
        for vlvl in lvlvl:
            lfnv.append(fd + "_" + "_".join(["at", str(vlvl), vlvl_unit]))
    
    return lfnv

def get_grib1id_from_cfname(cfname):
    """Return the tuple (IOP, ITL, LEV, TRI) corresponding to the given CF standard name.
    
    The tuples are first taken from table with default values.
    If the keyword "_at_" is present, ITL and LEV are modifed accordingly.
    
    
    Notes
    -----
    IOP: indicatorOfParameter
    ITL: indicationOfTypeOfLevel
    LEV: levelValue
    TRI: timeRangeIndicator
    
    
    Examples
    --------
    >>> get_grib1id_from_cfname("air_temperature_at_10_metres")
    >>> (11, 105, 10, 0)
    
    >>> get_grib1id_from_cfname("toa_outgoing_longwave_flux")
    >>> (114, 8, 0, 4)
    
    >>> get_grib1id_from_cfname("air_pressure_at_sea_level")
    >>> (1, 103, 0, 0)
    """
    base_quantity = cfname.split("_at_")[0]
    iop, itl, lev, tri = cfname_to_default_grib1id[base_quantity]
    
    if "_at_" in cfname:
        vlvl, unit = utils.lineparser(cfname, "_at_").split("_")
        if unit in unit_to_itl.keys():
            itl = unit_to_itl[unit]
            lev = int(vlvl)
        else:
            if unit == "level":
                # Case of "air_pressure_at_sea_level" and "air_pressure_at_surface_level"
                itl = 103 if vlvl == "sea" else 105
                lev = 0
            else:
                raise ValueError(f"Unknown vertical coordinate unit: {unit}")
    
    return iop, itl, lev, tri

def get_date_from_gribname(gribname):
    """Extract the date (1st of the month) from the GRIB name."""
    gribname = os.path.basename(gribname)
    _, _, year, month, _, _, _, _, _ = gribname.split("_")
    
    return dt.datetime(int(year), int(month), 1)

def get_grib1id_from_gribname(gribname):
    """Extract the tuple (IOP, ITL, LEV, TRI) from the GRIB name."""
    gribname = os.path.basename(gribname)
    _, _, _, _, iop, itl, lev, tri, _ = gribname.split("_")
    
    return iop, itl, lev, tri

def get_mera_gribname(varname, valtime, stream = "ANALYSIS", pathfromroot = False):
    """Return the name of the MERA GRIB file corresponding to the given variable
    
    MERA GRIB files follows the convention described in [TN65]:
        MERA_PRODYEAR_YYYY_MM_IOP_ITL_LEV_TRI_STREAM
    
    
    Parameters
    ----------
    varname: str or tuple of int
        Name of the variable. Either the CF standard name (str) or the tuple of GRIB1 indicators (IOP, ITL, LEV, TRI)
    
    valtime: `datetime.datetime`
        Time of validity of the data
    
    stream: str
        Stream of data ("ANALYSIS", "FC3hr" or "FC33hr")
    
    pathfromroot: bool
        If True, returns the path from the MERA root directory (i.e. the mount point for the reaext* drives)
    
    
    Returns
    -------
    gribname: str
        Name of the GRIB file containing the given variable at this validity time
    
    
    Examples
    --------
    >>> import datetime as dt
    >>> get_mera_gribname("air_pressure_at_sea_level", dt.datetime(2017, 10, 16, 18))
    >>> "MERA_PRODYEAR_2017_10_1_103_0_0_ANALYSIS"
    
    >>> get_mera_gribname("air_pressure_at_sea_level", dt.datetime(2017, 10, 16, 18), pathfromroot = True)
    >>> "mera/1/103/0/0/MERA_PRODYEAR_2017_10_1_103_0_0_ANALYSIS"
    """
    
    if isinstance(varname, str):
        iop, itl, lev, tri = get_grib1id_from_cfname(varname)
    else:
        iop, itl, lev, tri = varname
    
    gribname = "_".join(
        [
            str(s) for s in [
                "MERA", "PRODYEAR", valtime.year, str(valtime.month).zfill(2), iop, itl, lev, tri, stream
            ]
        ]
    )
    if pathfromroot:
        gribname = os.path.join(*[str(s) for s in ("mera", iop, itl, lev, tri)], gribname)
    
    return gribname

def expand_pathfromroot(gribname):
    """Returns the path from the MERA root directory (i.e. the mount point for the reaext* drives)
    
    
    Examples
    --------
    >>> expand_pathfromroot("MERA_PRODYEAR_2017_09_11_105_2_0_ANALYSIS")
    "mera/11/105/2/0/MERA_PRODYEAR_2017_09_11_105_2_0_ANALYSIS"
    """
    gribname = os.path.basename(gribname)
    iop, itl, lev, tri = get_grib1id_from_gribname(gribname)
    return os.path.join(*[str(s) for s in ("mera", iop, itl, lev, tri)], gribname)

def get_all_mera_gribnames(varnames, valtimes, streams = ["ANALYSIS"], pathfromroot = False):
    """Wrap-up the function get_mera_gribname in a loop"""
    gribnames = []
    for varname in varnames:
        for valtime in valtimes:
            for stream in streams:
                gribnames.append(get_mera_gribname(varname, valtime, stream, pathfromroot=pathfromroot))
            
        
    return np.unique(gribnames)

def get_filesystem_host_and_root(fsname):
    """Return the host name and the root path of the file system `fsname`
    
    The host name is either the IP adress or a name than can be reached with SSH
    or FTP and that contains the MERA data at the location given by the root path.
    
    
    Parameters
    ----------
    fsname: str
        File system name (reaext0*, all)
    
    
    Returns
    -------
    hostname: str
        Host name or IP adress where the file system is
    
    meraroot: str
        Path to the root directory of the file sytem.
    
    
    Examples
    --------
    The GRIB file MERA_PRODYEAR_2017_09_11_105_2_0_ANALYSIS is in the reaext03 filesystem.
    The output of this spinnet gives the command to copy this file locally.
    
    >>> gribname = "MERA_PRODYEAR_2017_09_11_105_2_0_ANALYSIS"
    >>> fsname = "reaext03"
    >>> rootgribname = expand_pathfromroot(gribname)
    >>> hostname, meraroot = get_filesystem_host_and_root(fsname)
    >>> abspath_to_grib = os.path.join(meraroot,rootgribname)
    >>> print(f"scp {hostname}:{abspath_to_grib} .")
    scp realin15:/run/media/trieutord/reaext03/mera/11/105/2/0/MERA_PRODYEAR_2017_09_11_105_2_0_ANALYSIS .
    """
    if fsname == "all":
        fstxt = os.path.join(_repopath_, "filesystems", "allmerafiles.txt")
    else:
        fstxt = os.path.join(_repopath_, "filesystems", f"merafiles_{fsname}.txt")
    
    hostname, meraroot = "", ""
    
    with open(fstxt, "r") as f:
        for l in f:
            if l.startswith("#!HOSTNAME="):
                hostname = utils.lineparser(l.strip(), "#!HOSTNAME=")
            if l.startswith("#!MERAROOT="):
                meraroot = utils.lineparser(l.strip(), "#!MERAROOT=")
            
            if len(hostname) > 0 and len(meraroot) > 0:
                break
    
    return hostname, meraroot


def read_variables_from_yaml(yaml_file):
    """Read the set of variables given in a yaml file. Vertical levels are expanded if necessary
    
    
    Parameters
    ----------
    yaml_file: str
        Path to the YAML file with a "variables" field
    
    
    Returns
    -------
    cfnames: list of str
        Flat list of CF standard names
    
    
    Examples
    --------
    >>> yaml_vars = {
        "variables":{
            "air_pressure_at_sea_level": {},
            "air_temperature":{
                    "levels": [2,10],
                    "level_unit": "metres"
                },
            }
        }
    >>> with open('test.yaml', 'w') as yf:
    >>>     yaml.dump(yaml_vars, yf)
    >>>
    >>> cfnames = read_variables_from_yaml('test.yaml')
    >>> cfnames
    ['air_pressure_at_sea_level', 'air_temperature_at_2_metres', 'air_temperature_at_10_metres']
    """
    with open(yaml_file, "r") as f:
        yf = yaml.safe_load(f)
    
    cfnames = []
    for v in yf["variables"]:
        if "levels" in yf["variables"][v].keys():
            assert "level_unit" in yf["variables"][v].keys(), f"Please provide a unit for the vertical level of {v}"
            
            level_unit = yf["variables"][v]["level_unit"]
            cfnames += [f"{v}_at_{lvl}_{level_unit}" for lvl in yf["variables"][v]["levels"]]
        else:
            cfnames.append(v)
        
    return cfnames

def write_variables_to_yaml(cfnames, yaml_file):
    """Write the set of variables into a yaml file.
    
    
    Parameters
    ----------
    cfnames: list of str
        Flat list of CF standard names
    
    yaml_file: str
        Path to the YAML file to be written
    
    
    Examples
    --------
    >>> cfnames = ['air_pressure_at_sea_level', 'air_temperature_at_2_metres', 'air_temperature_at_10_metres']
    >>> write_variables_to_yaml(cfnames, "test.yaml")
    >>> exit()
    sh> cat test.yaml
    variables:
      air_pressure_at_sea_level: {}
      air_temperature_at_10_metres: {}
      air_temperature_at_2_metres: {}
    """
    yaml_vars = {"variables":{v:{} for v in cfnames}}
    with open(yaml_file, 'w') as yf:
        yaml.dump(yaml_vars, yf)
    
def subset_present_variables(cfnames, fsname):
    """Return the subset of variables from `cfnames` that are found in the file system `fsname`
    
    
    Parameters
    ----------
    cfnames: list of str
        Larger set of variables
    
    fsname: str
        File system name (reaext0*, all)
    
    
    Returns
    -------
    herevarnames: list of str
        Subset of variables found in the file system
    
    
    Examples
    --------
    >>> cfnames = ['air_pressure_at_sea_level', 'air_temperature_at_2_metres', 'air_temperature_at_10_metres']
    >>> herevarnames = subset_present_variables(cfnames, "reaext03")
    ['air_pressure_at_sea_level', 'air_temperature_at_2_metres']
    """
    if fsname == "all":
        fstxt = os.path.join(_repopath_, "filesystems", "allmerafiles.txt")
    else:
        fstxt = os.path.join(_repopath_, "filesystems", f"merafiles_{fsname}.txt")
    
    with open(fstxt, "r") as f:
        ll = f.readlines()
    
    merafilenames = []
    for l in ll:
        if l.startswith("MERA"):
            merafilenames.append(l.strip())
    
    iop_itl_lev_tri = [
        "_".join([str(d) for d in get_grib1id_from_cfname(cfname)])
        for cfname in cfnames
    ]
    
    herevarnames = []
    for varcode, varname in zip(iop_itl_lev_tri, cfnames):
        n_files_here = len([fn for fn in merafilenames if varcode in fn])
        
        if n_files_here > 0:
            herevarnames.append(varname)
        
    return herevarnames

def subset_present_gribnames(gribnames, fsname, exclude_bz2 = True):
    """Return the subset of GRIB files from `gribnames` that are found in the file system `fsname`
    
    
    Parameters
    ----------
    cfnames: list of str
        Requested set of GRIB files
    
    fsname: str
        File system name (reaext0*, all)
    
    
    Returns
    -------
    herevarnames: list of str
        Subset of GRIB files found in the file system
    
    
    Examples
    --------
    >>> gribnames = ["MERA_PRODYEAR_2017_09_11_105_2_0_ANALYSIS", "MERA_PRODYEAR_2017_10_11_105_2_0_ANALYSIS", "MERA_PRODYEAR_2017_10_11_105_10_0_ANALYSIS"]
    >>> heregribnames = subset_present_gribnames(gribnames, "reaext03", False)
    ["MERA_PRODYEAR_2017_09_11_105_2_0_ANALYSIS", "MERA_PRODYEAR_2017_10_11_105_2_0_ANALYSIS"]
    """
    if fsname == "all":
        fstxt = os.path.join(_repopath_, "filesystems", "allmerafiles.txt")
    else:
        fstxt = os.path.join(_repopath_, "filesystems", f"merafiles_{fsname}.txt")
    
    with open(fstxt, "r") as f:
        ll = f.readlines()
    
    fsgribnames = []
    for l in ll:
        if exclude_bz2:
            keep = l.startswith("MERA") and not l.endswith(".bz2")
        else:
            keep = l.startswith("MERA")
        
        if keep:
            fsgribnames.append(l.strip())
    
    gribnames = [os.path.basename(fn) for fn in gribnames]
    if not exclude_bz2:
        gribnames += [fn + ".bz2" for fn in gribnames]
        
    return list(set(fsgribnames) & set(gribnames))

def get_all_present_gribnames(cfnames, fsname, exclude_bz2 = True, stream = "ANALYSIS"):
    """Return the subset of GRIB files from `gribnames` that are found in the file system `fsname`
    
    
    Parameters
    ----------
    cfnames: list of str
        Requested set of GRIB files
    
    fsname: str
        File system name (reaext0*, all)
    
    
    Returns
    -------
    herevarnames: list of str
        Subset of GRIB files found in the file system
    
    
    Examples
    --------
    >>> cfnames = ['air_pressure_at_sea_level', 'air_temperature_at_2_metres']
    >>> heregribnames = get_all_present_gribnames(cfnames, "reaext03", False)
    ["MERA_PRODYEAR_2017_09_11_105_2_0_ANALYSIS", "MERA_PRODYEAR_2017_10_11_105_2_0_ANALYSIS"]
    """
    if fsname == "all":
        fstxt = os.path.join(_repopath_, "filesystems", "allmerafiles.txt")
    else:
        fstxt = os.path.join(_repopath_, "filesystems", f"merafiles_{fsname}.txt")
    
    with open(fstxt, "r") as f:
        ll = f.readlines()
    
    iop_itl_lev_tri = [
        "_".join([str(d) for d in get_grib1id_from_cfname(cfname)] + [stream])
        for cfname in cfnames
    ]
    
    fsgribnames = []
    for l in ll:
        l = l.strip()
        keep = l.startswith("MERA") and any([vc in l for vc in iop_itl_lev_tri])
        if exclude_bz2:
            keep = keep and not l.endswith(".bz2")
        
        if keep:
            fsgribnames.append(l)
    
    return fsgribnames

def uncompress_bz2(bz2file):
    """Uncompress a bz2 file at the same location with the same name (without the .bz2 suffix)"""
    with bz2.BZ2File(bz2file) as fr, open(bz2file[:-4], "wb") as fw:
        shutil.copyfileobj(fr,fw)
    
    os.remove(bz2file)
    
    return bz2file[:-4]

def uncompress_all_bz2(rootdir, verbose = False):
    """Browse all sub-directories of `rootdir` and uncompress bz2 when they are found"""
    i = 0
    for root, dirs, files in os.walk(rootdir):
        for f in files:
            if f.endswith(".bz2"):
                uncompress_bz2(os.path.join(root, f))
                i += 1
                if i % 10 == 0:
                    print(f"[{i} files uncompressed] last one: {f}")


def count_dates_per_month(dates_available, dates_expected = None):
    """Count 
    """
    if dates_expected is not None:
        start = min(dates_expected)
        stop = max(dates_expected)
    else:
        start = min(dates_available)
        stop = max(dates_available)
    
    years = np.arange(start.year, stop.year + 1)
    months = np.arange(1, 13)
    
    if dates_expected is not None:
        msg = "  Counting #(dates availables) - #(dates expected) for each month   \n"
    else:
        msg = "  Counting number of dates availables for each month   \n"
    
    msg += "     |" + " ".join([str(m).ljust(5) for m in months]) + "\n"
    msg += "-----+" + "-".join(["-----" for m in months]) + "\n"
    mcount = np.zeros((years.size, 12), dtype = np.int32)
    for iy, y in enumerate(years):
        for m in months:
            if dates_expected is not None:
                mcount[iy, m-1] = sum([d.year == y and d.month == m for d in dates_available]) - sum([d.year == y and d.month == m for d in dates_expected])
            else:
                mcount[iy, m-1] = sum([d.year == y and d.month == m for d in dates_available])
        
        msg += str(y).ljust(5) + "|" + " ".join(
            [
                str(mc).ljust(5) for mc in mcount[iy, :]
            ]
        ) + "\n"
    
    msg += "-----+" + "-".join(["-----" for m in months]) + "\n"
    print(msg)
    
    return mcount

# EOF
