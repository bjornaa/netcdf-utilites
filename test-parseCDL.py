# -*- coding: utf-8 -*-

import unittest

import numpy as np
from parse_CDL import parse_dimension, parse_variable, parse_attribute
from parse_CDL import join_lines, split_lines


class TestParseDimension(unittest.TestCase):
    """Testing the parse_dimension function"""

    def test_ordinary(self):
        """Test ordinary (limited) dimensions"""
        line = 'lon = 360'
        name, length, isunlimited = parse_dimension(line)
        self.assertEqual(name, 'lon')
        self.assertEqual(length, 360)
        self.assertFalse(isunlimited)

        line = 'lon=360'
        name, length, isunlimited = parse_dimension(line)
        self.assertEqual(name, 'lon')

    def test_unlimited(self):
        """Test an unlimited dimension"""
        line = 'time = unlimited'
        name, length, isunlimited = parse_dimension(line)
        self.assertEqual(name, 'time')
        self.assertEqual(length, 0)
        self.assertTrue(isunlimited)


class TestParseVariable(unittest.TestCase):
    """Testing the parse_variable function"""

    def test_variable(self):
        line = 'float temperature(time, lat, lon)'
        name, nctype, shape = parse_variable(line)
        self.assertEqual(name, 'temperature')
        self.assertEqual(nctype, 'float')
        self.assertEqual(shape, ('time', 'lat', 'lon'))

    def test_variable_nodim(self):
        line = 'int version'
        name, nctype, shape = parse_variable(line)
        self.assertEqual(name, 'version')
        self.assertEqual(nctype, 'int')
        self.assertEqual(shape, ())


class TestParseAttribute(unittest.TestCase):
    """Testing the parse_attribute function"""

    def test_ASCII(self):
        """Handle strings correctly"""
        line = 'var:att = "ASCII text" ;'
        var, name, value = parse_attribute(line)
        self.assertEqual(var, 'var')
        self.assertEqual(name, 'att')
        self.assertEqual(value, 'ASCII text')

    def test_unicode(self):
        """Handle unicode strings correctly"""
        line = u'var:author = "Bjørn Ådlandsvik" ;'
        var, name, value = parse_attribute(line)
        self.assertEqual(var, 'var')
        self.assertEqual(name, u'author')
        self.assertEqual(value, u'Bjørn Ådlandsvik')

    def test_scalar(self):
        line1 = ':three = 3s'
        line2 = ':three = 3'
        line3 = 'var:pi = 3.14f'
        line4 = 'var:pi = 3.14159'
        var, name, value = parse_attribute(line1)
        self.assertEqual(var, None)
        self.assertEqual(name, 'three')
        self.assertEqual(value, np.array([3], dtype='int16'))
        var, name, value = parse_attribute(line2)
        self.assertEqual(name, 'three')
        self.assertEqual(value, np.array([3], dtype='int32'))
        var, name, value = parse_attribute(line3)
        self.assertEqual(name, 'pi')
        self.assertEqual(value, np.array([3.14], dtype='float32'))
        var, name, value = parse_attribute(line4)
        self.assertEqual(name, 'pi')
        self.assertEqual(value, np.array([3.14159]))

    def test_vector(self):
        line1 = ':a = 1s, 2, 3s'
        line2 = ':a = 1, 2, 3'
        line3 = ':a = 1.0f, 2e16f, -4.2e11'
        line4 = ':a = 1.0, 2e16, -4.2e11'
        var, name, value = parse_attribute(line1)
        self.assertEqual(var, None)
        self.assertEqual(name, 'a')
        self.assertTrue(np.alltrue(value ==
                        np.array([1, 2, 3], dtype='int16')))
        var, name, value = parse_attribute(line2)
        self.assertEqual(name, 'a')
        self.assertTrue(np.alltrue(value ==
                        np.array([1, 2, 3], dtype='int32')))
        var, name, value = parse_attribute(line3)
        self.assertEqual(name, 'a')
        self.assertTrue(np.alltrue(value == np.array([1., 2e16, -4.2e11],
                                                     dtype='float32')))
        var, name, value = parse_attribute(line4)
        self.assertEqual(name, 'a')
        self.assertTrue(np.alltrue(value == np.array([1., 2e16, -4.2e11])))


class TestLineHandling(unittest.TestCase):

    def test_join(self):
        lines = ['This is the first line',
                 'logically it continues and ends here;',
                 'This is the second logical line;']
        log_lines = join_lines(lines)
        line = next(log_lines)
        expected = " ".join([lines[0], lines[1].rstrip(';')])
        self.assertEqual(line, expected)
        line = next(log_lines)
        expected = lines[2].rstrip(';')
        self.assertEqual(line, expected)

    def test_split(self):
        double_line = 'First line; Second line'
        log_lines = split_lines([double_line])
        line = next(log_lines)
        self.assertEqual(line, 'First line')
        line = next(log_lines)
        self.assertEqual(line, ' Second line')


if __name__ == '__main__':
    unittest.main()
