#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The Met Eireann ReAnalysis explorer

Write GRIBs extracted from MERA for Neural-LAM initialisation.
"""
import argparse
from mera_explorer import forecasts

parser = argparse.ArgumentParser(
    prog="write_gribs_for_neurallam_init.py",
    description="Write GRIBs extracted from MERA for Neural-LAM initialisation.",
    epilog="Example: python write_gribs_for_neurallam_init.py --sdate 2017-01-01 --edate 2017-02-01 --outdir test",
)
parser.add_argument(
    "--sdate",
    help="Start date in ISO format - YYYY-MM-DD HH:MM",
)
parser.add_argument(
    "--edate",
    help="End date in ISO format - YYYY-MM-DD HH:MM",
)
parser.add_argument("--step", help="Time step between each leadtime", default="3h")
parser.add_argument("--max-leadtime", help="Maximum lead time", default="54h")
parser.add_argument(
    "--textract", help="Frequency of files to be extracted", default="72h"
)
parser.add_argument(
    "--outdir",
    help="Frequency of files to be extracted",
    default=forecasts.DEFAULT_ROOTDIR,
)
args = parser.parse_args()

forecasts.DEFAULT_ROOTDIR = args.outdir
forecasts.create_mera_analysis_and_forcings(
    startdate=args.sdate,
    enddate=args.edate,
    max_leadtime=args.max_leadtime,
    textract=args.textract,
    step=args.step,
)
