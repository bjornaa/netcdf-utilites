# -*- coding: utf-8 -*-

"""Exercise 1 from Unidata's NcML tutorial

http://www.unidata.ucar.edu/
software/thredds/current/netcdf-java/ncml/Tutorial.html
"""

import sys
from ncstructure import NCstructure

struc = NCstructure.from_NcML('exercise1.ncml')

struc.write_CDL(sys.stdout)

