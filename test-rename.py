# coding=utf-8

import unittest

from ncstructure import NCstructure


class TestDimension(unittest.TestCase):

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
        self.assertEqual(struc.dimensions.keys(), ['a', 'bb', 'c'])
        # Variable shape is updated correctly
        self.assertEqual(var.shape, ('a', 'bb'))

    def test_wrong_dimension(self):
        struc = NCstructure('test')
        struc.createDimension('lon', 360)
        with self.assertRaises(KeyError):
            struc.renameDimension('longitude', 'latitude')


if __name__ == '__main__':
    unittest.main()
