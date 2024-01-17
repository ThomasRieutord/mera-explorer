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
import yaml
import numpy as np
import datetime as dt
from mera_explorer import utils

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

def get_mera_gribname(varname, valtime, stream = "ANALYSIS", pathfromroot = False):
    """Return the name of the MERA GRIB file corresponding to the given variable
    
    MERA GRIB files follows the convention described in [TN65]:
        MERA_PRODYEAR_YYYY_MM_IOP_ITL_LEV_TRI_STREAM
    
    
    Parameters
    ----------
    varname: str or tuple of int
        Name of the variable. Either the CF standard name (str) or the tuple of GRIB1 indicators (IOP, ITL, LEV, TRI)
    
    valtime: datetime.datetime
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

def get_all_mera_gribnames(varnames, valtimes, streams = ["ANALYSIS"], pathfromroot = False):
    """Wrap-up the function get_mera_gribname in a loop"""
    gribnames = []
    for varname in varnames:
        for valtime in valtimes:
            for stream in streams:
                gribnames.append(get_mera_gribname(varname, valtime, stream, pathfromroot=pathfromroot))
            
        
    return np.unique(gribnames)

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
            "air_pressure_at_mean_sea_level": {},
            "air_temperature":{
                    "levels": [2,10],
                    "level_unit": "meters"
                },
            }
        }
    >>> with open('test.yaml', 'w') as yf:
    >>>     yaml.dump(yaml_vars, yf)
    >>>
    >>> cfnames = read_variables_from_yaml('test.yaml')
    >>> cfnames
    ['air_pressure_at_mean_sea_level', 'air_temperature_at_2_meters', 'air_temperature_at_10_meters']
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
    >>> cfnames = ['air_pressure_at_mean_sea_level', 'air_temperature_at_2_meters', 'air_temperature_at_10_meters']
    >>> write_variables_to_yaml(cfnames, "test.yaml")
    >>> exit()
    sh> cat test.yaml
    variables:
      air_pressure_at_mean_sea_level: {}
      air_temperature_at_10_meters: {}
      air_temperature_at_2_meters: {}
    """
    yaml_vars = {"variables":{v:{} for v in cfnames}}
    with open(yaml_file, 'w') as yf:
        yaml.dump(yaml_vars, yf)
    
