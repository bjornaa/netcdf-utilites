# -*- coding: utf-8 -*-

import os
import unittest
import subprocess
import filecmp
import codecs

from netcdf_utilities.ncstructure import NCstructure


class TestNcML(unittest.TestCase):

    def setUp(self):
        """Make a ncml-file from from a cdl-file"""
        # Use ncgen to make test.nc
        subprocess.call(['ncgen', '-b', 'test.cdl'])
        # Use ncdump to make test.ncml
        with open('test.ncml', 'w') as fid:
            subprocess.call(['ncdump', '-x', 'test.nc'], stdout=fid)

    def test_NcML(self):
        """from_NcML followed by write_NcML should restore the NcML-file"""
        nc = NCstructure.from_NcML('test.ncml')
        with codecs.open('mytest.ncml', 'w', encoding='utf-8') as fid:
            nc.write_NcML(fid)
        self.assertTrue(filecmp.cmp('mytest.ncml', 'test.ncml'))

    def tearDown(self):
        os.remove('test.nc')
        os.remove('test.ncml')
        os.remove('mytest.ncml')


if __name__ == '__main__':
    unittest.main()
