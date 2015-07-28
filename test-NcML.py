# -*- coding: utf-8 -*-

# import sys
import unittest
import subprocess
import filecmp
import codecs
# import numpy as np
from ncstructure import *

# sys.stdout = codecs.getwriter('utf8')(sys.stdout)

# Use ncgen, ncdump on test.cdl to generate an NcML file
subprocess.call(['ncgen', '-b', 'test.cdl'])  # Make test.nc
with open('test.ncml', 'w') as ncmlfid:
    subprocess.call(['ncdump', '-x', 'test.nc'], stdout=ncmlfid)


class TesNcML(unittest.TestCase):
    def test_write_NcML(self):
        structure = NCstructure.from_file('test.nc')  # Get the structure from the NetCDF file
        with codecs.open('mytest.ncml', mode='w', encoding='utf-8') as fid:
            structure.write_NcML(fid)

        self.assertTrue(filecmp.cmp('mytest.ncml', 'test.ncml'))


if __name__ == '__main__':
    unittest.main()
