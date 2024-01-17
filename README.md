The Met Eireann ReAnalysis explorer
========================
In 2016, the Irish national meteorological service ([Met Eireann](https://www.met.ie/)) produced an [atmospheric reanalysis](https://en.wikipedia.org/wiki/Atmospheric_reanalysis): the Met Eireann ReAnalysis, or [MERA](https://www.met.ie/climate/available-data/mera).
The main purpose of this repository is provide tools to browse and manipulate the data from this reanalysis.

<img src="assets/MERA-topo-300x300.png" width="300" />


Installation
------------

### With Conda (only way for now)

The main dependencies of this repository are Python 3.10, Eccodes, Ecml-tools, Xarray, Numpy, Zarr, h5py, netCDF4 and Matplotlib.
We recommend to use [Conda](https://docs.conda.io/projects/conda/en/latest/index.html).
In a Conda environment with the listed packages, clone the repository and install the package with `pip install -e .`


### Check the installation

To check the software installation:
```
python tests/import_tests.py
````


Usage
------

### Know if the data you want is available in MERA

  1. Edit the YAML file at `mera_explorer/data/mydata.yaml` to list all the variables you want
  2. Launch `python scripts/is_my_data_there.py [--fs=FILESYSTEM] [--vars=YAMLFILE]`


### Help transferring the data

Not implemented yet.


### Convert the data into a different format

Not implemented yet.



More infos
----------

### About

For the time being (Jan. 2024) MERA data are scattered in several places: part of it (the most commonly used variables) are stored in HDD read manually by the staff at Met Eireann HQ, another part of it (the less commonly used variables) are stored in the ECFS facility retrieved and read with ECFS tools.
The current code only browse the file systems of the HDD (exported in the `reaext/*.txt`) and the list of variables provided by the document describing MERA.
To get access to the data (after you checked if it is there with this code), ask Eoin Whelan (eoin.whelan@met.ie) or Emily Gleeson (emily.gleeson@met.ie).


### License:

All rights reserved.
