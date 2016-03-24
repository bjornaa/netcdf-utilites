# -*- coding: utf-8 -*-

import os
# import unittest
import subprocess
# import filecmp
# import codecs

from netcdf_utilities.ncstructure import NCstructure
from netcdf_utilities.ncgen import ncgen

def test_ncgen():

    ncstruc = NCstructure.from_CDL('test.cdl')

    with open('a.py', mode='w') as f:
        ncgen(ncstruc, f)

    # Use a.py to generate a.nc
    subprocess.call(['python', 'a.py'])
    os.rename('test.nc', 'a.nc')

    # Generate test.nc directly from test.cdl
    subprocess.call(['ncgen', '-b', 'test.cdl'])

    # Check that the files are identical
    return_code = subprocess.call(['cmp', 'a.nc', 'test.nc'])
    assert(return_code == 0)

    # Clean up
    os.unlink('a.py')
    os.unlink('a.nc')
    os.unlink('test.nc')
