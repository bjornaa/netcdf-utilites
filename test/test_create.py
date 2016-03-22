# -*- coding: utf-8 -*-

import unittest

from netcdf_utilities.ncstructure import NCstructure


class TestCreate(unittest.TestCase):
    def test_empty_structure(self):
        struc0 = NCstructure()
        self.assertEqual(struc0.location, None)
        self.assertFalse(struc0.dimensions)
        self.assertFalse(struc0.variables)
        self.assertFalse(struc0.attributes)

    def test_structure(self):
        # Define a structure
        struc = NCstructure('test')
        struc.createDimension('lon', 360)
        struc.createDimension('time', 0, isUnlimited=True)
        var = struc.createVariable('time', 'double', ('time',))
        var.createAttribute('name', 'time')
        var.createAttribute('units', 'seconds since 1948-01-01 00:00:00')
        var = struc.createVariable('u', 'float', ('time', 'lon'))
        var.createAttribute('units', 'meter second-1')
        struc.createAttribute('institution', 'Institute of Marine Research')
        struc.createAttribute('author', 'Bjørn Ådlandsvik')
        # Check the structure
        self.assertEqual(struc.location, 'test')  # go for test.nc ??
        self.assertEqual(struc.dimensions['lon'].length, 360)
        self.assertFalse(struc.dimensions['lon'].isUnlimited)
        self.assertTrue(struc.dimensions['time'].isUnlimited)
        uvar = struc.variables['u']
        self.assertEqual(uvar.shape, ('time', 'lon'))
        self.assertEqual(uvar.nctype, 'float')
        self.assertEqual(uvar.attributes['units'].value, 'meter second-1')
        self.assertEqual(struc.attributes['institution'].name, 'institution')
        # Can the above avoided?
        self.assertEqual(struc.attributes['institution'].value,
                         'Institute of Marine Research')

    def test_missing_dimension(self):
        struc = NCstructure('test')
        struc.createDimension('lon', 360)
        with self.assertRaises(AssertionError):
            # struc does not have a latitude dimension
            struc.createVariable('temperature', 'float', ('lat', 'lon'))


if __name__ == '__main__':
    unittest.main()
