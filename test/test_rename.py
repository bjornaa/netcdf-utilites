# -*- coding=utf-8 -*-

import unittest

from netcdf_utilities.ncstructure import NCstructure


class TestRenameDimension(unittest.TestCase):

    def test_no_rename(self):
        struc = NCstructure('test')
        dim = struc.createDimension('lon', 360)

        with self.assertRaises(AttributeError):
            dim.name = 'longitude'
        self.assertEqual(dim.name, struc.dimensions['lon'].name)

    def test_rename(self):
        struc = NCstructure('test')
        struc.createDimension('a', 10)
        struc.createDimension('b', 20)
        struc.createDimension('c', 30)
        var = struc.createVariable('lon', 'float', ('a', 'b'))
        id0 = id(struc.dimensions['b'])
        struc.renameDimension('b', 'bb')

        # Same dimension
        self.assertEqual(id(struc.dimensions['bb']), id0)
        # Correct name
        self.assertEqual(struc.dimensions['bb'].name, 'bb')
        # Correct place in OrderedDict
        self.assertEqual(list(struc.dimensions.keys()), ['a', 'bb', 'c'])
        # Variable shape is updated correctly
        self.assertEqual(var.shape, ('a', 'bb'))

    def test_wrong_dimension(self):
        struc = NCstructure('test')
        struc.createDimension('lon', 360)
        with self.assertRaises(KeyError):
            struc.renameDimension('longitude', 'latitude')


class TestRenameVariable(unittest.TestCase):

    def test_no_rename(self):
        struc = NCstructure('test')
        struc.createDimension('lon', 360)
        var = struc.createVariable('lon', 'float', ('lon',))
        with self.assertRaises(AttributeError):
            var.name = 'longitude'
        self.assertEqual(var.name, struc.variables['lon'].name)

    def test_rename(self):
        struc = NCstructure('test')
        struc.createDimension('lon', 360)
        struc.createVariable('a', 'float', ('lon',))
        struc.createVariable('b', 'float', ('lon',))
        struc.createVariable('c', 'float', ('lon',))
        id0 = id(struc.variables['b'])
        struc.renameVariable('b', 'bb')

        # Same variable
        self.assertEqual(id(struc.variables['bb']), id0)
        # Correct name
        self.assertEqual(struc.variables['bb'].name, 'bb')
        # Correct place in OrderedDict
        self.assertEqual(list(struc.variables.keys()), ['a', 'bb', 'c'])

    def test_wrong_variable(self):
        struc = NCstructure('test')
        struc.createDimension('lon', 360)
        struc.createVariable('lon', 'float', ('lon',))
        with self.assertRaises(KeyError):
            struc.renameVariable('longitude', 'latitude')


class TestRenameAttribute(unittest.TestCase):

    def test_rename(self):
        struc = NCstructure('test')
        struc.createDimension('lon', 360)
        var = struc.createVariable('lon', 'float', ('lon',))
        struc.createAttribute('type', 'Global test attribute')
        var.createAttribute('long_name', 'longitude')

        struc.renameAttribute('type', 'newtype')
        self.assertEqual(struc.attributes['newtype'].name, 'newtype')
        var.renameAttribute('long_name', 'standard_name')
        self.assertEqual(var.attributes['standard_name'].name, 'standard_name')

if __name__ == '__main__':
    unittest.main()
