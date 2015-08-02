# -*- coding: utf-8 -*-

import unittest

from ncstructure import *


class TestParseAttribute(unittest.TestCase):

    def test_ASCII(self):
        """Handle strings correctly"""
        line = 'var:att = "ASCII text" ;'
        name, value = parse_attribute(line)
        self.assertEqual(name, 'att')
        self.assertEqual(value, 'ASCII text')

    def test_unicode(self):
        """Handle unicode strings correctly"""
        line = u'var:author = "Bjørn Ådlandsvik" ;'
        name, value = parse_attribute(line)
        self.assertEqual(name, u'author')
        self.assertEqual(value, u'Bjørn Ådlandsvik')

    def test_scalar(self):
        line1 = ':three = 3s ;'
        line2 = ':three = 3 ;'
        line3 = 'var:pi = 3.14f ;'
        line4 = 'var:pi = 3.14159 ;'
        name, value = parse_attribute(line1)
        self.assertEqual(name, 'three')
        self.assertEqual(value, np.array([3], dtype='int16'))
        name, value = parse_attribute(line2)
        self.assertEqual(name, 'three')
        self.assertEqual(value, np.array([3], dtype='int32'))
        name, value = parse_attribute(line3)
        self.assertEqual(name, 'pi')
        self.assertEqual(value, np.array([3.14], dtype='float32'))
        name, value = parse_attribute(line4)
        self.assertEqual(name, 'pi')
        self.assertEqual(value, np.array([3.14159]))

    def test_vector(self):
        line1 = ':a = 1s, 2, 3s ;'
        line2 = ':a = 1, 2, 3 ;'
        line3 = ':a = 1.0f, 2e16f, -4.2e11 ;'
        line4 = ':a = 1.0, 2e16, -4.2e11 ;'
        name, value = parse_attribute(line1)
        self.assertEqual(name, 'a')
        self.assertTrue(np.alltrue(value == np.array([1, 2, 3], dtype='int16')))
        name, value = parse_attribute(line2)
        self.assertEqual(name, 'a')
        self.assertTrue(np.alltrue(value == np.array([1, 2, 3], dtype='int32')))
        name, value = parse_attribute(line3)
        self.assertEqual(name, 'a')
        self.assertTrue(np.alltrue(value == np.array([1., 2e16, -4.2e11],
                                                     dtype='float32')))
        name, value = parse_attribute(line4)
        self.assertEqual(name, 'a')
        self.assertTrue(np.alltrue(value == np.array([1., 2e16, -4.2e11])))

if __name__ == '__main__':
    unittest.main()
