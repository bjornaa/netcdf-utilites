# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import unittest
import numpy as np

#from ncstructure import Attribute, Attributes


class TestAttribute(unittest.TestCase):
    def rest_create(self):
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
        target = "Attribute('batches', 'int', [2 3])"
        self.assertEqual(repr(att), target)

        att = Attribute('min_depth', np.array(10, dtype=np.int16))
        target = "Attribute('min_depth', 'short', [10])"
        self.assertEqual(repr(att), target)

    def rest_attributes_attributes(self):
        """Test python attributes of a netCDF attribute"""
        att = Attribute('units', 'meter')
        self.assertEqual(att.name, 'units')
        self.assertEqual(att.value, 'meter')
        self.assertEqual(att.type, 'String')

        att = Attribute('version', 3.14)
        self.assertEqual(att.name, 'version')
        self.assertEqual(att.value, np.array([3.14]))
        self.assertEqual(att.type, 'double')

    def rest_type(self):
        att = Attribute('version', 2)
        self.assertEqual(att.type, 'int') # 'long' in netCDF4
        att = Attribute('version', np.array(2, dtype=np.int16))
        self.assertEqual(att.type, 'short')
        att = Attribute('version', np.array(2, dtype=np.int32))
        self.assertEqual(att.type, 'int')
        att = Attribute('version', np.array(2, dtype=np.int64))
        self.assertEqual(att.type, 'int') # 'long' in netCDF4

        att = Attribute('version', np.array(3.14))
        self.assertEqual(att.type, 'double')
        att = Attribute('version', np.array(3.14, dtype=np.float32))
        self.assertEqual(att.type, 'float')
        att = Attribute('version', np.array(3.14, dtype=np.float64))
        self.assertEqual(att.type, 'double')


class TestAttributes(unittest.TestCase):

    def rest_create(self):
         A = Attributes()

         imr = 'Institute of Marine Research'
         inst = Attribute('institution', imr)

         A.append(inst)
         A.append(Attribute('version', 2.0))

         self.assertEqual(A['institution'].value, imr)
         self.assertEqual(A['institution'].name, 'institution')
         self.assertEqual(A['version'].value, 2.0)


    def rest_iterate(self):
        A = Attributes()
        names = ['att{}'.format(i) for i in range(4)]
        values = ['value{}'.format(i) for i in range(4)]
        for name, value in zip(names, values):
            A.append(Attribute(name, value))

        for i, att in enumerate(A):
            self.assertEqual(att.name, names[i])
            self.assertEqual(att.value, values[i])


if __name__ == '__main__':
    unittest.main()
