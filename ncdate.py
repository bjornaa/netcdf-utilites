#! /usr/bin/env python
# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------
# usage: ncdate.py [-h] [-r RECORD] [-t TIME_VARIABLE] file
#
# Display the time in a netCDF file
#
# positional arguments:
#   file                  Name of netCDF file
#
# optional arguments:
#   -h, --help            show this help message and exit
#   -r RECORD, --record RECORD
#                       record number, defaults to 0 i.e. first record
#  -t TIME_VARIABLE, --time-variable TIME_VARIABLE
#                        name of time variable
# ---------------------------------------------------------------------

# If no time variable is specified, it will use 
# a unique time variable in the file (1D and with "since" in units)
# None or multiple time variables in the file give error.
#
# Record numbers follows the python convention:
# The default --record=0 gives the first record
# Negative numbers count from the end, in particular
# --record=-1 gives the last record in the file

# The script requires the netcdf4-python package
# It should work with both python 2.7 and 3.x

# ----------------------------------
# Bjørn Ådlandsvik <bjorn@imr.no>
# Institute of Marine Research
# 2015-06-12
# ----------------------------------

# -----------
# Imports
# -----------

import sys
from argparse import ArgumentParser

try:
    from netCDF4 import Dataset, num2date
except ImportError:
    print("ERROR: netcdf4-python is not installed")
    sys.exit(1)

# ------------------------
# Command line arguments
# ------------------------

aparser = ArgumentParser(description="Display the time in a netCDF file")

# File name
aparser.add_argument('file', help='Name of netCDF file')

# Record option
aparser.add_argument('-r', '--record', type=int, default=0,
                     help='record number, defaults to 0 i.e. first record')

# Time variable option
aparser.add_argument('-t', '--time-variable',
                     help="name of time variable")

args = aparser.parse_args()

# ----------------------
# The NetCDF file
# ----------------------

try:
    fid = Dataset(args.file)
except RuntimeError:
    print("Can not open netcdf file: {}".format(args.file))
    sys.exit(1)

# --------------
# Time variable
# --------------


# Check function for time variables
# Criterium: 1D and "since" in units
def is_time_variable(name):
    """Check if a variables is a time variable"""
    answer = False
    var = fid.variables[name]
    if var.ndim == 1:
        if 'units' in var.ncattrs():
            if 'since' in var.units:
                answer = True
    return answer

if args.time_variable is None:
    # No time variable specified
    # check the file for time variables

    timevars = []
    for var_name in fid.variables:
        if is_time_variable(var_name):
            timevars.append(var_name)

    if len(timevars) == 0:
        print("ERROR: No time variable")
        sys.exit(1)

    if len(timevars) > 1:
        print("ERROR: Multiple time variables")
        print(timevars)
        print("Use --time-variable option")
        sys.exit(1)

    timevar = timevars[0]

else:  # Time variable specified with --time-variable option

    # Check the time variable
    timevar = args.time_variable
    # Is it defined?
    try:
        tvar = fid.variables[timevar]
    except KeyError:
        print("ERROR: Can not find variable {}".format(timevar))
        sys.exit(1)
    # Is it a time variable?
    if not is_time_variable(timevar):
        print("ERROR: Variable {} is not a time variable".format(timevar))

# -------------------
# Get the time value
# -------------------

tvar = fid.variables[timevar]

try:
    time_value = tvar[args.record]
except IndexError:
    print("ERROR: Must have -{ntimes} <= record < {ntimes}".
          format(ntimes=len(tvar)))
    sys.exit(1)

# Use the netcdf4-python function num2date to parse the time
date = num2date(time_value, tvar.units)

print(date)
