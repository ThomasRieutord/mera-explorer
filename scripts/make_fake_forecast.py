#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The Met Eireann ReAnalysis explorer

Make fake forecasts in GRIBs files, starting from pre-computed MERA analysis.
"""
# python -i make_fake_forecast.py --sdate 2017-01-01 --edate 2017-02-01 --max-leadtime 65h --forecaster neurallam
import os
import argparse
from mera_explorer import forecasts
from neural_lam import forecasters
from neural_lam import package_rootdir as NLAMPKRDIR

parser = argparse.ArgumentParser(
    prog="make_fake_forecast.py",
    description="Make fake forecasts in GRIBs files starting from MERA analysis.",
    epilog="Example: python make_fake_forecast.py --sdate 2017-01-01 --edate 2017-02-01 --forecaster persistence",
)
parser.add_argument(
    "--sdate",
    help="Start date in ISO format - YYYY-MM-DD HH:MM",
)
parser.add_argument(
    "--edate",
    help="End date in ISO format - YYYY-MM-DD HH:MM",
)
parser.add_argument(
    "--forecaster",
    help="The type of fake forecast (persistence, gradientincrement; see neural_lam.forecasters)",
    default="persistence",
)
parser.add_argument("--step", help="Time step between each leadtime", default="3h")
parser.add_argument("--max-leadtime", help="Maximum lead time", default="54h")
parser.add_argument(
    "--textract", help="Frequency of files to be extracted", default="72h"
)
args = parser.parse_args()

if args.forecaster == "persistence":
    fakefc = forecasters.Persistence()
elif args.forecaster == "gradientincrement":
    fakefc = forecasters.GradientIncrement()
elif args.forecaster == "neurallam":
    fakefc = forecasters.NeuralLAMforecaster(
        # "/home/dutr/neural-lam/saved_models/graph_lam-4x64-06_27_12-9867/min_val_loss.ckpt"
        os.path.join(NLAMPKRDIR, "saved_models", "graph_lam-4x64-07_19_15-2217", "min_val_loss.ckpt")
    )
    # forecasts.SUBSAMPLING_STEP = 2
else:
    raise ValueError(
        f"Unknown fake forecast option {args.forecaster}. See neural_lam.forecasters to have vaild options"
    )

forecasts.forecast_from_analysis_and_forcings(
    startdate=args.sdate,
    enddate=args.edate,
    forecaster=fakefc,
    max_leadtime=args.max_leadtime,
    textract=args.textract,
    step=args.step,
)


# # Tests
# from mera_explorer import MERACLIMDIR, MERAROOTDIR, PACKAGE_DIRECTORY, gribs, utils
# import torch

# basetime = utils.str_to_datetime("2017-01-01")
# analysis = forecasts.get_analysis(basetime)
# forcings = forecasts.get_forcings(basetime)
# borders = forecasts.get_borders(basetime, "65h")

# analysis, forcings, borders = [torch.tensor(_) for _ in (analysis, forcings, borders)]
# analysis, forcings, borders = [_.unsqueeze(0).float() for _ in (analysis, forcings, borders)]
# print(f"Shapes: analysis={analysis.shape}, forcings={forcings.shape}, borders={borders.shape}")
