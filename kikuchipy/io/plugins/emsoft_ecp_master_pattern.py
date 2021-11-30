# -*- coding: utf-8 -*-
# Copyright 2019-2021 The kikuchipy developers
#
# This file is part of kikuchipy.
#
# kikuchipy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# kikuchipy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kikuchipy. If not, see <http://www.gnu.org/licenses/>.

"""Read support for simulated electron channeling pattern (ECP) master
patterns in EMsoft's HDF5 format.
"""

from typing import List, Optional

from kikuchipy.io.plugins._emsoft_master_pattern import EMsoftMasterPatternReader


# Plugin characteristics
# ----------------------
format_name = "emsoft_ecp_master_pattern"
description = (
    "Read support for electron channeling pattern (ECP) master patterns"
    " stored in EMsoft's HDF5 file format."
)
full_support = False
# Recognised file extension
file_extensions = ["h5", "hdf5"]
default_extension = 0
# Writing capabilities
writes = False

# Unique HDF5 footprint
footprint = ["emdata/ecpmaster"]


class EMsoftECPMasterPatternReader(EMsoftMasterPatternReader):
    diffraction_type = "ECP"
    cl_parameters_group_name = "MCCL"  # Monte Carlo openCL
    energy_string = "EkeV"


def file_reader(
    filename: str,
    energy: Optional[range] = None,
    projection: str = "stereographic",
    hemisphere: str = "north",
    lazy: bool = False,
    **kwargs,
) -> List[dict]:
    """Read simulated electron channeling pattern (ECP) master patterns
    from EMsoft's HDF5 file format :cite:`callahan2013dynamical`.

    Parameters
    ----------
    filename
        Full file path of the HDF file.
    energy
        Desired beam energy or energy range. If None is passed
        (default), all available energies are read.
    projection
        Projection(s) to read. Options are "stereographic" (default) or
        "lambert".
    hemisphere
        Projection hemisphere(s) to read. Options are "north" (default),
        "south" or "both". If "both", these will be stacked in the
        vertical navigation axis.
    lazy
        Open the data lazily without actually reading the data from disk
        until requested. Allows opening datasets larger than available
        memory. Default is False.
    kwargs :
        Keyword arguments passed to h5py.File.

    Returns
    -------
    signal_dict_list: list of dicts
        Data, axes, metadata and original metadata.
    """
    reader = EMsoftECPMasterPatternReader(
        filename=filename,
        energy=energy,
        projection=projection,
        hemisphere=hemisphere,
        lazy=lazy,
    )
    return reader.read(**kwargs)
