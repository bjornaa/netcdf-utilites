# -*- coding: utf-8 -*-

import unittest

from ncstructure import *

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO  # python 3


class TestWriteCDL(unittest.TestCase):
    def test_empty(self):
        """Test an empty structure"""
        # Make an empty netCDF structure
        struc0 = NCstructure('a.nc')
        # Write the CDL
        output = StringIO()
        struc0.write_CDL(output)
        # Check the CDL
        target = "netcdf a {\n}\n"  # ncdump of empty file
        assert (output.getvalue() == target)

    def test_dimensions_only(self):
        """Test a structure with only dimensions"""
        struc0 = NCstructure('a.nc')
        # Add a dimension
        struc0.createDimension('X', 10)
        # Write the CDL
        output = StringIO()
        struc0.write_CDL(output)
        # Check the CDL
        target = "netcdf a {\ndimensions:\n\tX = 10 ;\n}\n"  # ncdump
        assert (output.getvalue() == target)

    def test_global_att_only(self):
        struc0 = NCstructure('a.nc')  # Empty structure
        struc0.createAttribute('purpose', 'test')
        output = StringIO()
        struc0.write_CDL(output)
        lines = ['netcdf a {\n',
                 '// global attributes:',
                 '\t\t:purpose = "test" ;',
                 '}\n']
        target = '\n'.join(lines)
        assert (output.getvalue() == target)


if __name__ == '__main__':
    unittest.main()
