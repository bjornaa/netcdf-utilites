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

