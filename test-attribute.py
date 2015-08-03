# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import unittest

from ncstructure import Attribute


class TestAttribute(unittest.TestCase):
    def test_create(self):
        # Create some dimensions and check their repr
        att = Attribute('units', 'meter')
        target = "Attribute('units', 'String', 'meter')"
        self.assertEqual(repr(att), target)
        
        att = Attribute(value='Bjørn Ådlandsvik', name='author')
        target = "Attribute('author', 'String', 'Bjørn Ådlandsvik')"
        target = target.encode('utf-8')
        self.assertEqual(repr(att), target)

        att = Attribute('version', 3.14)
        target = "Attribute('version', 'double', [ 3.14])"
        self.assertEqual(repr(att), target)

        att = Attribute('batches', (2, 3))
        target = "Attribute('version', 'int', [ 2 3])"
        self.assertEqual(repr(att), target)
        

        
        
    ##     lon = Dimension('lon', 360)
    ##     lat = Dimension(length=181, name='lat')
    ##     time = Dimension('time', 0, isUnlimted=True)
    ##     self.assertEqual(repr(lon), "Dimension('lon', 360)")
    ##     self.assertEqual(repr(lat), "Dimension('lat', 181)")
    ##     self.assertEqual(repr(time), "Dimension('time', 0, isUnlimited=True)")

    ## def test_missing_length(self):
    ##     """Missing argument should raise TypeError"""
    ##     self.assertRaises(TypeError, Dimension, 'lon')

    ## def test_attributes(self):
    ##     lon = Dimension('lon', 360)
    ##     self.assertEqual(lon.name, 'lon')
    ##     self.assertEqual(lon.length, 360)
    ##     self.assertEqual(lon.isUnlimited, False)
    ##     self.assertEqual(len(lon), 360)

        # def test_noassign


## class TestDimensions(unittest.TestCase):
##     def test_create(self):
##         D = Dimensions()
##         time = Dimension('time', 0, isUnlimited=True)
##         D.append(time)
##         D.append(Dimension(length=181, name='lat'))
##         D.append(Dimension('lon', 360))

##         # Make better representation f.ex. Dimensions('time', 'lon', 'lat')
##         self.assertEqual(repr(D), "time, lat, lon")

##         self.assertEqual(D['time'], time)

##         self.assertEqual(D['lon'].name, 'lon')
##         self.assertEqual(D['lon'].length, 360)
##         self.assertEqual(D['lon'].isUnlimited, False)

##         # Test iteration
##         names = [dim.name for dim in D]
##         targets = ['time', 'lat', 'lon']
##         for name, target in zip(names, targets):
##             self.assertEqual(name, target)


if __name__ == '__main__':
    unittest.main()
