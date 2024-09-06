#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The Met Eireann ReAnalysis explorer

Plot forecast for Ophelia initialised with GRIB extracted from MERA.
"""
import argparse
import os

import cartopy.crs as ccrs
import numpy as np

from mera_explorer import NEURALLAM_VARIABLES, forecasts, gribs, utils
from metplotlib import plots
from neural_lam import PACKAGE_ROOTDIR as NEURALLAM_PACKAGE_ROOTDIR
from neural_lam import forecasters

parser = argparse.ArgumentParser(
    prog="ophelia_foreacst_plot.py",
    description="Plot forecast for Ophelia initialised with GRIB extracted from MERA.",
    epilog="Example: python -i ophelia_foreacst_plot.py --forecaster neurallam:graph_lam-4x64-09_03_18-2112 --figdir test",
)
parser.add_argument(
    "--forecaster",
    help="The type of fake forecast (persistence, gradientincrement; see neural_lam.forecasters)",
    default="persistence",
)
parser.add_argument("--max-leadtime", help="Maximum lead time", default="54h")
parser.add_argument("--figdir", help="Output directory for figures", default="")
parser.add_argument("--figfmt", help="Format for the figures (png, svg)", default="png")
parser.add_argument(
    "--device",
    help="Device on which the inference is run ('cpu' or 'cuda')",
    default="cpu",
)
args = parser.parse_args()

figdir = args.figdir
figfmt = "." + args.figfmt
os.makedirs(figdir, exist_ok=True)

if args.forecaster == "persistence":
    forecaster = forecasters.Persistence()
elif args.forecaster == "gradientincrement":
    forecaster = forecasters.GradientIncrement()
elif args.forecaster.startswith("neurallam"):
    modelid = args.forecaster.split(":")[1]
    forecaster = forecasters.NeuralLAMforecaster(
        os.path.join(
            NEURALLAM_PACKAGE_ROOTDIR, "saved_models", modelid, "min_val_loss.ckpt"
        ),
        device=args.device,
    )
else:
    raise ValueError(
        f"Unknown fake forecast option {args.forecaster}. See neural_lam.forecasters to have vaild options"
    )

OPHELIA_LANDFALL_DATE = "2017-10-16 00:00"

basetime = utils.str_to_datetime(OPHELIA_LANDFALL_DATE)
max_leadtime = utils.str_to_timedelta(args.max_leadtime)
step = utils.str_to_timedelta("3h")

# Get the reference
# -----------------
ref_states = forecasts.get_borders(
    basetime, max_leadtime, concat=False, data_scaler=None
)

# Get the forecast
# ----------------
analysis = forecasts.get_analysis(basetime, data_scaler=forecaster.data_scaler)
print(f"Analysis: {analysis.shape}")
forcings = forecasts.get_forcings(basetime, flux_scaler=forecaster.flux_scaler)
print(f"Forcings: {forcings.shape}")
borders = forecasts.get_borders(
    basetime, max_leadtime, data_scaler=forecaster.data_scaler
)
print(f"Borders: {borders.shape}")
forecast = forecaster.forecast(analysis, forcings, borders)
forecast = forecaster.data_scaler.inverse_transform(forecast)
print(f"Forecast done: {forecast.shape}")

gridshape = ref_states[0]["air_pressure_at_sea_level"].shape
fc_states = forecasts.separate_states(forecast, NEURALLAM_VARIABLES, gridshape)


# Make the plots
# ----------------
titles = np.array(
    [
        ["Predicted", "Target"],
        ["Diff (MSLP)", "Diff (T2m)"],
    ]
)
crs = ccrs.LambertConformal(**gribs.get_mera_crs(fmt="cartopy"))

if args.forecaster.startswith("neurallam"):
    bw = (
        forecaster.model.border_mask.reshape(gridshape).sum(axis=0).min().short().item()
    )
else:
    bw = 1

gribname = forecasts.get_path_from_times(basetime, "0h", "mera")
lon, lat = gribs.get_lonlat_grid(gribname)
lon = lon[bw:-bw, bw:-bw]
lat = lat[bw:-bw, bw:-bw]

figpaths = []
n_figures = min(len(ref_states), len(fc_states))
for i, (ref, fc) in enumerate(zip(ref_states[:n_figures], fc_states[:n_figures])):

    bar = "=" * i + " " * (n_figures - i)
    print(f"Creating figures:\t [{bar}] ({i}/{n_figures})", end= "\r")

    valtime = basetime + (i + 1) * step
    true_mslp = ref["air_pressure_at_sea_level"] / 100
    pred_mslp = fc["air_pressure_at_sea_level"] / 100
    true_t2m = ref["air_temperature_at_2_metres"] - 273.15
    pred_t2m = fc["air_temperature_at_2_metres"] - 273.15

    # Crop the borders
    pred_mslp = pred_mslp[bw:-bw, bw:-bw]
    true_mslp = true_mslp[bw:-bw, bw:-bw]
    pred_t2m = pred_t2m[bw:-bw, bw:-bw]
    true_t2m = true_t2m[bw:-bw, bw:-bw]

    fig, ax = plots.twovar_comparison(
        true_mslp,
        pred_mslp,
        true_t2m,
        pred_t2m,
        lons=lon,
        lats=lat,
        cl_varfamily="temp",
        figcrs=crs,
        # datcrs=crs,
        titles=titles,
    )
    fig.suptitle(
        f"Ophelia - valtime={valtime.strftime('%Y-%m-%d %H:%M')} (+{(i+1)*3}h)"
    )
    figpath = os.path.join(
        figdir,
        f"ophelia_{forecaster.shortname}_{valtime.strftime('%Y%m%d%H')}" + figfmt,
    )
    fig.savefig(figpath)
    figpaths.append(figpath)

print(f"Figures stored in {figdir}. Creating and animated GIF now")
gifpath = os.path.join(figdir, f"ophelia_{forecaster.shortname}.gif")
cmd = f"convert -delay 60 -loop 0 {' '.join(figpaths)} {gifpath}"
os.system(cmd)
print(f"Done: {gifpath}")
