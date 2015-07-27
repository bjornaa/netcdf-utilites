#! /usr/bin/env python
# -*- coding: utf-8 -*-

# -------------------------------------------------------------------
# Convert float/double variables in a netCDF file to 16-bit integers
# Usage:
# float2int16.py [-h] [-3] infile outfile
#
# Convert float/double to 16-bit integers
#
# positional arguments:
#   infile      Name of input netCDF file
#   outfile     Name of output file
#
# optional arguments:
#   -h, --help  show this help message and exit
#   -3          Create netCDF-3 format instead of default netCDF-4
# -------------------------------------------------------------------

# ---------------------------------------------
# Bjørn Ådlandsvik <bjorn@imr.no>
# Institute of Marine Research, Bergen, Norway
# ---------------------------------------------

# --------
# Imports
# --------

import sys
from argparse import ArgumentParser
import collections

try:
    import numpy as np
except ImportError:
    print("ERROR: numpy is not installed")
    sys.exit(1)

try:
    from netCDF4 import Dataset
except:
    print("ERROR: netcdf4-python is not installed")
    sys.exit(1)

# -------------------------
# User settings: Configure the conversion
# -------------------------


# Varibles to convert into 16-bit integers
# Format: variable = Rescale(scale_factor, add_offset)
Rescale = collections.namedtuple('Rescale', ('scale_factor', 'add_offset'))
scale_dictionary = dict(
    zeta = Rescale(0.01, 0.0),
    ubar = Rescale(0.001, 0.0),
    vbar = Rescale(0.001, 0.0),
    u    = Rescale(0.001, 0.0),
    v    = Rescale(0.001, 0.0),
    temp = Rescale(0.001, 10.0),
    salt = Rescale(0.001, 30.0),
    Akt  = Rescale(0.01, 0.0),
    Aks  = Rescale(0.01, 0.0),
)

# List of variables to not copy
dont_copy = ['omega']

# --- End user settings ---

# ----------
# Constants
# ----------

UNDEF = -32767  # 1 - 2**15

# ------------------------
# Command line arguments
# ------------------------

aparser = ArgumentParser(description="Convert float/double to 16-bit integers")

aparser.add_argument('-3', dest='format', action='store_const',
                     const='NETCDF3_CLASSIC', default='NETCDF4_CLASSIC',
                     help='Create netCDF-3 format instead of default netCDF-4')

# File names
aparser.add_argument('infile', help='Name of input netCDF file')
aparser.add_argument('outfile', help='Name of output file')

args = aparser.parse_args()

# -------------------
# Inspect input file
# -------------------

f0 = Dataset(args.infile)

# Find unlimited dimension, if any
# Classic format has at most one
unlim_dim = None
numrec = 0      # Number of records
for name in f0.dimensions:
    dim = f0.dimensions[name]
    if dim.isunlimited():
        unlim_dim = name
        numrec = len(dim)
        break

# Classify input variables
all_vars = f0.variables.keys()
for v in dont_copy:
    try:
        all_vars.remove(v)
    except ValueError:
        pass  # Don't bark if variable v is missing already

record_vars = [v for v in all_vars if unlim_dim in f0.variables[v].dimensions]
nonrec_vars = [v for v in all_vars if v not in record_vars]

# -------------------------------
# Create output file
# -------------------------------

f1 = Dataset(args.outfile, mode='w', format=args.format)

# -----------------------
# Copy global attributes
# -----------------------

for name in f0.ncattrs():
    setattr(f1, name, getattr(f0, name))

# ------------------
# Copy dimensions
# ------------------

for name, dim in f0.dimensions.items():
    if dim.isunlimited():
        f1.createDimension(name, 0)
    else:
        f1.createDimension(name, len(dim))

# ---------------------
# Variable definitions
# ---------------------
for name in f0.variables:
    v0 = f0.variables[name]
    if name in scale_dictionary:
        v1 = f1.createVariable(name, 'i2', v0.dimensions,
                               fill_value=UNDEF, zlib=True)
    else:
        if '_fillValue' in v0.ncattrs():
            f1.createVariable(name, v0.dtype, v0.dimensions,
                              fill_value=v0._fillValue)
        else:
            f1.createVariable(name, v0.dtype, v0.dimensions)

# Variable attributes
for name in f0.variables:
    v0 = f0.variables[name]
    v1 = f1.variables[name]
    for att in v0.ncattrs():
        if att != "_fillValue":
            setattr(v1, att, getattr(v0, att))
    if name in scale_dictionary:
        v1.scale_factor = scale_dictionary[name].scale_factor
        v1.add_offset = scale_dictionary[name].add_offset

# ----------------
# Non-record data
# ----------------

for name in nonrec_vars:
    v0 = f0.variables[name]
    v1 = f1.variables[name]
    v0.set_auto_maskandscale(False)
    v1.set_auto_maskandscale(False)
    if (name in scale_dictionary) and (v0.dtype != dtype('int16')):
        # Convert from float/double to int 16
        scale_factor = scale_dictionary[name].scale_factor
        offset = scale_dictionary[name].add_offset
        values = (v0[:] - offset) / scale
        values[np.abs(values) > abs(UNDEF)] = scale*UNDEF + offset
        v1[:] = np.round(values).astype('int16')
    else:  # No conversion
        v1[:] = v0[:]

# Take record variables record per record
for name in record_vars:
    v0 = f0.variables[name]
    v1 = f1.variables[name]
    v0.set_auto_maskandscale(False)
    v1.set_auto_maskandscale(False)
    if (name in scale_dictionary) and (v0.dtype != np.dtype('int16')):
        # Convert from float/double to int 16
        for rec in xrange(numrec):
            scale = scale_dictionary[name].scale_factor
            offset = scale_dictionary[name].add_offset
            values = (v0[rec, ...] - offset) / scale
            values[np.abs(values) > abs(UNDEF)] = scale*UNDEF + offset
            v1[rec, ...] = np.round(values).astype('int16')
    else:  # No conversion
        for rec in xrange(numrec):
            v1[rec, ...] = v0[rec, ...]

# ----------
# Clean up
# ----------
f1.close()
