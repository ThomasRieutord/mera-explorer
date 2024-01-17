#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The Met Eireann ReAnalysis explorer.

Data about the NeuralLAM project (see Useful links and References).


Useful links
------------
The NeuralLAM Github page
    https://github.com/joeloskarsson/neural-lam

The NeuralLAM ArXiv preprint
    https://arxiv.org/abs/2309.17370


References
----------
[Osk23] Oskarsson, J., Landelius, T., & Lindsten, F. (2023).
        Graph-based Neural Weather Prediction for Limited Area Modeling.
        arXiv preprint arXiv:2309.17370.
"""

from mera_explorer import gribs


# Variables listed in Neural-LAM (from [Osk23], appendix C, table 1)
# -----------------------------
neurallam_variables = [
    "air_pressure_at_surface_level",
    "air_pressure_at_sea_level",
    "net_upward_longwave_flux_in_air",
    "net_upward_shortwave_flux_in_air",
    "atmosphere_mass_content_of_water_vapor",
] + gribs.add_vlevel_to_fieldnames(
    ["relative_humidity", "air_temperature"],
    [2, 60],    # In MEPS, the first level is at 65 m. We take 60 instead.
    "metres"
) + gribs.add_vlevel_to_fieldnames(
    ["eastward_wind", "northward_wind"],
    [60],    # In MEPS, the first level is at 65 m. We take 60 instead.
    "metres"
) + gribs.add_vlevel_to_fieldnames(
    ["geopotential"],
    [1000],
    "hPa"
) + gribs.add_vlevel_to_fieldnames(
    ["eastward_wind", "northward_wind", "air_temperature"],
    [850],
    "hPa"
) + gribs.add_vlevel_to_fieldnames(
    ["geopotential", "air_temperature"],
    [500],
    "hPa"
)

neurallam_variables_grib1ids = {
    v:gribs.get_grib1id_from_cfname(v) for v in neurallam_variables
}


# Additional variables to look at (personal choice, for testing purposes)
# -------------------------------
additional_variables = [
    "precipitation_amount",
    "land_binary_mask",
    "surface_roughness_length",
    "surface_albedo",
    "vegetation_area_fraction",
    "cloud_area_fraction",
    "toa_net_upward_shortwave_flux",
    "toa_outgoing_longwave_flux",
] + gribs.add_vlevel_to_fieldnames(
    ["eastward_wind", "northward_wind"], [10], "metres"
) + gribs.add_vlevel_to_fieldnames(
    ["eastward_wind", "northward_wind", "upward_air_velocity", "air_temperature"], [700], "hPa"
)

additional_variables_grib1ids = {v:gribs.get_grib1id_from_cfname(v) for v in additional_variables}


# All variables
# -------------
all_variables = neurallam_variables + additional_variables

if __name__ == "__main__":
    from pprint import pprint
    print(f"{len(neurallam_variables)} Neural-LAM variables:")
    pprint(neurallam_variables_grib1ids)
    print(f"{len(additional_variables)} Additional variables:")
    pprint(additional_variables_grib1ids)
    
    print("\nYAML exports: " + "  \n".join(
        [
            "gribs.write_variables_to_yaml(neurallam_variables, 'neurallam.yaml')",
            "gribs.write_variables_to_yaml(all_variables, 'neurallam-all.yaml')",
        ]
    ))
