#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The Met Eireann ReAnalysis explorer.

Test transfers
"""

import os
import numpy as np
from mera_explorer import transfer
import argparse


parser = argparse.ArgumentParser(prog="transfer_test", description='Check if the data is at the correct location and in the correct format.')
parser.add_argument('--local', help="Test a local transfer", action='store_true')
parser.add_argument('--ftp', help="Test a transfer with FTP", action='store_true')
parser.add_argument('--ssh', help="Test a transfer with SSH", action='store_true')
args = parser.parse_args()


# Set up the test
# ---------------
os.makedirs("tmp/src")
os.makedirs("tmp/trg")

loc_srcs = [f"tmp/src/transfertestfile_{i}.txt" for i in range(20)]
loc_trgs = [f"tmp/trg/transfertestfile_{i}.txt" for i in range(20)]
rem_trgs = [f"tmp/transfertestfile_{i}.txt" for i in range(20)]

for src in loc_srcs:
    x = np.random.rand(100, 100)
    np.savetxt(src, x)

remotehost = "reaserve"
rusername = "trieutord"


# Instanciate the transfer
# ------------------------

if args.local:
    trf = transfer.LocalTransfer()
if args.ssh:
    trf = transfer.SSHTransfer(remotehost, rusername)
if args.ftp:
    trf = transfer.FTPTransfer(remotehost, rusername)

print(trf)


# Make the transfer way and back
# ------------------------
print(f"Sending {len(loc_srcs)} files from {trf.localhost} to {trf.remotehost}")
trf.mput(loc_srcs, rem_trgs)
print(f"Getting back the files from {trf.remotehost} to {trf.localhost}")
trf.mget(rem_trgs, loc_trgs)

print("Done. >>> meld tmp/src tmp/trg (directories should be the same)")
print("Clean up: [local]>>> rm -r tmp    [remote]>>> rm ~/tmp/transfertestfile_*")
