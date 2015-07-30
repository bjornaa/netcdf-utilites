# -*- coding: utf-8 -*-

import os
import unittest
import subprocess
import filecmp
import codecs

from ncstructure import NCstructure


class TestCDL(unittest.TestCase):

    def setUp(self):
        """Standardize the CDL file"""
        # Use ncgen to make test.nc
        subprocess.call(['ncgen', '-b', 'test.cdl'])
        # Use ncdump to generate a well-behaved CFL-file
        with open('test0.cdl', 'w') as fid:
            subprocess.call(['ncdump', '-h', 'test.nc'], stdout=fid)

    def test_CDL(self):
        """from_CDL followed bu write_CDL restore the CDL-file"""
        nc = NCstructure.from_CDL('test.cdl')
        with codecs.open('mytest.cdl', 'w', encoding='utf-8') as fid:
            nc.write_CDL(fid)

        self.assertTrue(filecmp.cmp('mytest.cdl', 'test0.cdl'))

    def tearDown(self):
        os.remove('test.nc')
        os.remove('test0.cdl')
        os.remove('mytest.cdl')


if __name__ == '__main__':
    unittest.main()
