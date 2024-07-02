#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The Met Eireann ReAnalysis explorer

Make fake forecasts in GRIBs files, starting from pre-computed MERA analysis.
"""
import argparse
from mera_explorer import forecasts
from neural_lam import forecasters

parser = argparse.ArgumentParser(
    prog="make_fake_forecast.py",
    description="Make fake forecasts in GRIBs files starting from MERA analysis.",
    epilog="Example: python make_fake_forecast.py --sdate 2017-01-01 --edate 2017-02-01  --forecaster persistence",
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
