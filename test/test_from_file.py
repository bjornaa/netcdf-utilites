# -*- coding: utf-8 -*-

import os
import unittest
import subprocess
import filecmp
import codecs

from netcdf_utilities.ncstructure import NCstructure


class TestFromFile(unittest.TestCase):

    def setUp(self):
        """Standardize the CDL file"""
        # Use ncgen to make test.nc
        subprocess.call(['ncgen', '-b', 'test.cdl'])
        # Use ncdump to generate a well-behaved CFL-file
        with open('test0.cdl', 'w') as fid:
            subprocess.call(['ncdump', '-h', 'test.nc'], stdout=fid)

    def test_from_file(self):
        """from_netCDF followed by write_CDL restore the CDL-file"""
        # Create the structure
        nc = NCstructure.from_file('test.nc')

        # Check the structure, by comparing CDL to the one generated by ncdump
        with codecs.open('mytest.cdl', 'w', encoding='utf-8') as fid:
            nc.write_CDL(fid)
        self.assertTrue(filecmp.cmp('mytest.cdl', 'test0.cdl'))

    def tearDown(self):
        os.remove('test.nc')
        os.remove('test0.cdl')
        os.remove('mytest.cdl')

if __name__ == '__main__':
    unittest.main()
