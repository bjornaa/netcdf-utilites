NetCDF Utilities
================

This is a placeholder for small python scripts some general for
handling netCDF files and some may be more special for netCDF files
related to the ocean model ROMS.

Bjørn Ådlandsvik <bjorn@imr.no>
Institute of Marine Research, Bergen, Norway

ncdate.py - Print the dates in a netCDF file
--------------------------------------------

Time in a netCDF is most often given by the CF-standard
(coming from the older udunits library). These may be
difficult to parse manually. This utility does this job.

Usage: ncdate.py [-h] [-r RECORD] [-t TIME_VARIABLE] file


If no time variable is specified, it will use 
a unique time variable in the file (1D and with "since" in units)
None or multiple time variables in the file give error.

Record numbers follows the python convention:
The default --record=0 gives the first record
Negative numbers count from the end, in particular
--record=-1 gives the last record in the file

float2int16.py - Convert float/double to short
----------------------------------------------

Convert selected float/double variables to short integers

Usage:
float2int16.py [-h] [-3] infile outfile

Convert float/double to 16-bit integers

positional arguments:
  infile      Name of input netCDF file
  outfile     Name of output file

optional arguments:
  -h, --help  show this help message and exit
  -3          Create netCDF-3 format instead of default netCDF-4

The script must be edited to modify the dictionary `scale_dictionary`
to specify what variables to convert and their scale_factor and add_offset.
The list `dont_copy` specifies variables that should
not be copied/converted.

By default, the output file is in netCDF-4 format, with internal
zlib-compression.

