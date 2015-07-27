# -*- coding: utf-8 -*-

# import sys
import unittest
import subprocess
import StringIO
# import numpy as np
from ncstructure import *

# sys.stdout = codecs.getwriter('utf8')(sys.stdout)

# Use ncgen, ncdump on test.cdl to generate the true answer
subprocess.call(['ncgen', '-b', 'test.cdl'])
fasit = subprocess.check_output(['ncdump', '-h', 'test.nc']).decode('utf-8')
fasit = fasit.splitlines()


class TestCDL(unittest.TestCase):
    def test_correct(self):
        nc = NCstructure.from_CDL('test.cdl')
        output = StringIO.StringIO()
        nc.write_CDL(output)

        output.seek(0)  # Rewind output for comparison
        for i, line in enumerate(output):
            self.assertEqual(line.rstrip('\n'), fasit[i])


if __name__ == '__main__':
    unittest.main()
