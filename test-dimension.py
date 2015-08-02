# -*- coding: utf-8 -*-

import unittest

from ncstructure import Dimension, Dimensions


class TestDimension(unittest.TestCase):
    def test_create(self):
        # Create some dimensions and check their repr

        lon = Dimension('lon', 360)
        lat = Dimension(length=181, name='lat')
        time = Dimension('time', 0, isUnlimited=True)
        self.assertEqual(repr(lon), "Dimension('lon', 360)")
        self.assertEqual(repr(lat), "Dimension('lat', 181)")
        self.assertEqual(repr(time), "Dimension('time', 0, isUnlimited=True)")

    def test_missing_length(self):
        """Missing argument should raise TypeError"""
        self.assertRaises(TypeError, Dimension, 'lon')

    def test_attributes(self):
        lon = Dimension('lon', 360)
        self.assertEqual(lon.name, 'lon')
        self.assertEqual(lon.length, 360)
        self.assertEqual(lon.isUnlimited, False)
        self.assertEqual(len(lon), 360)

        # def test_noassign


class TestDimensions(unittest.TestCase):
    def test_create(self):
        D = Dimensions()
        time = Dimension('time', 0, isUnlimited=True)
        D.append(time)
        D.append(Dimension(length=181, name='lat'))
        D.append(Dimension('lon', 360))

        # Make better representation f.ex. Dimensions('time', 'lon', 'lat')
        self.assertEqual(repr(D), "time, lat, lon")

        self.assertEqual(D['time'], time)

        self.assertEqual(D['lon'].name, 'lon')
        self.assertEqual(D['lon'].length, 360)
        self.assertEqual(D['lon'].isUnlimited, False)

        # Test iteration
        names = [dim.name for dim in D]
        targets = ['time', 'lat', 'lon']
        for name, target in zip(names, targets):
            self.assertEqual(name, target)


if __name__ == '__main__':
    unittest.main()
