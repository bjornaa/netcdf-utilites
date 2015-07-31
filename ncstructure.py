# -*- coding: utf-8 -*-

"""
ncstructure:

Class for structure of a classic netCDF file

"""

# Ha klassemetoder
# from_CDL, from_NcML
# Lag tekst til python funksjon som definerer filen
#

from __future__ import unicode_literals

import sys
import os
from collections import OrderedDict
import itertools as it
import codecs
from xml.etree import ElementTree

import numpy as np
from netCDF4 import Dataset

PY2 = sys.version_info[0] == 2
# PY3 = sys.version_info[0] == 3

# Ensure stdout is OK
if PY2:
    sys.stdout = codecs.getwriter('utf8')(sys.stdout)

# Follow six convention
string_type = str  # python 3
if PY2:
    string_type = basestring

# Mapping from dtype.char or python type to NetCDF type
# NCtype = {float: 'double',
#           int  : 'int',
#           str  : 'char',
#           'd'  : 'double',
#           'f'  : 'float',
#           'i'  : 'int',
#           'h'  : 'short',
#           'b'  : 'byte',
#           'S'  : 'char',
#           'U'  : 'char',
#           }

# Conversion from numpy dtype.char to NetCDF type
NCtype = dict(h='short', i='int', f='float', d='double')

# Conversion from nctype to numpy dtype
dtype = dict(short=np.int16, int=np.int32, float=np.float32, double=np.float64)


# if PY2:
#    NCtype[unicode] = 'char'


class Dimension(object):
    """NetCDF dimensjon"""

    def __init__(self, name, length=0, isunlimited=False):
        self.name = name
        self.length = length
        self.isUnlimited = isunlimited


class _Attribute(object):
    """NetCDF attribute"""

    def __init__(self, value):
        if isinstance(value, string_type):
            self.value = value
            self.type = 'String'
        else:
            self.value = np.atleast_1d(value)
            self.type = NCtype[np.asarray(value).dtype.char]


class _HasNCAttributes(object):
    # Open for kwargs
    def __init__(self):
        self.attributes = OrderedDict()

    def set_attribute(self, key, value):
        self.attributes[key] = _Attribute(value)

    # Hva om attribute ikke finnes?
    def delete_attribute(self, key):
        del self[key]

    def ncattrs(self):
        return self.attributes.keys()


class Variable(_HasNCAttributes):
    """NetCDF variable"""

    # Ta attributter som ekstra argumenter
    def __init__(self, ncstructure, name, nctype, shape=()):
        self.structure = ncstructure
        self.name = name
        self.nctype = nctype
        self.shape = shape
        # self.ndim = len(self.dimensions)
        _HasNCAttributes.__init__(self)


class NCstructure(_HasNCAttributes):
    def __init__(self, location=None):
        self.location = location
        self.dimensions = OrderedDict()
        self.variables = OrderedDict()
        _HasNCAttributes.__init__(self)

    def add_dimension(self, dimension):
        self.dimensions.setdefault(dimension.name, dimension)

    def add_variable(self, variable):
        self.variables.setdefault(variable.name, variable)

    @classmethod
    def from_file(cls, filename):
        """Extract the structure from a netCDF file"""

        # kutt om ikke netCDF fil
        with Dataset(filename) as fid:
            nc = cls(location=filename)

            for name, dim in fid.dimensions.items():
                d = Dimension(name, len(dim), dim.isunlimited())
                nc.add_dimension(d)

            for name, var in fid.variables.items():
                # Slå sammen til createVariable
                v = Variable(ncstructure=nc, name=name,
                             nctype=NCtype[var.dtype.char],
                             shape=var.dimensions)
                nc.add_variable(v)
                # Variable attributes
                for att in var.ncattrs():
                    value = getattr(var, att)
                    v.set_attribute(att, value)

            # Global attributes
            for att in fid.ncattrs():
                value = getattr(fid, att)
                nc.set_attribute(att, value)

        return nc

    # ---

    @classmethod
    def from_CDL(cls, filename):
        """Define the data structure from a CDL file"""
        fid = codecs.open(filename, encoding='utf-8')

        nc = NCstructure()

        # Skip empty lines
        lines = (line for line in fid if line.split())

        # Location line
        words = next(lines).split()
        nc.location = words[1]

        # Dimensions
        next(lines)  # Skip "dimensions:"
        dimlines = it.takewhile(lambda x: x.split()[0] != 'variables:', lines)
        for line in dimlines:
            words = line.split()
            isunlimited = (words[2].upper() == 'UNLIMITED')
            if isunlimited:
                # Get size from comment
                size = int(words[5][1:])  # Skip "(" in
            else:
                size = int(words[2])
            nc.add_dimension(Dimension(words[0], size, isunlimited))

        # Variables
        def isvarline(line):
            w = line.split()
            # Global attributes comes after comment line
            # not ending with ";"
            return w[-1][-1] == ';'

        variable_lines = it.takewhile(isvarline, lines)
        # Split the variables
        variable_chunks = isplit_noloss(lambda x: ':' in x.split()[0],
                                        variable_lines)

        for chunk in variable_chunks:
            words = chunk[0].split()  # main variable line
            words = [w.rstrip(',') for w in words]  # strip trailing commas
            nctype = words[0]
            if '(' in words[1]:  # has dimensions
                ndim = len(words) - 2
                name, dim0 = words[1].split('(')
                dims = [dim0]
                for i in range(1, ndim):
                    dims.append(words[i + 1])
                dims[-1] = dims[-1][:-1]  # remove trailing ')'
            else:
                name = words[1]
                ndim = 0
                dims = []
            # print name, nctype, tuple(dims)
            # Uelegant med de to linjene under, kombinere til en
            var = Variable(nc, name, nctype, tuple(dims))
            nc.add_variable(var)
            # Attribute lines
            for line in chunk[1:]:
                name, value = parse_attribute(line)
                var.set_attribute(name, value)

        # Global attributes
        globatt_lines = it.takewhile(lambda x: x.lstrip().startswith(':'),
                                     lines)
        for line in globatt_lines:
            name, value = parse_attribute(line)
            nc.set_attribute(name, value)

        return nc

    @classmethod
    def from_NcML(cls, filename):

        # Parse the NcML file
        with open(filename) as fid:
            tree = ElementTree.parse(fid)

        root = tree.getroot()

        # Create the structure
        nc = NCstructure()

        nc.location = root.attrib['location']

        # Get iterators for the toplevel things,
        #     dimensions, global attributes and variables
        main_groups = it.groupby(root, key=lambda s: s.tag.split('}')[1])

        for key, group in main_groups:

            # Dimensions
            if key == 'dimension':
                for node in group:
                    name = node.attrib['name']
                    length = node.attrib['length']
                    isunlimited = 'isUnlimited' in node.attrib.keys()
                    nc.add_dimension(Dimension(name, length, isunlimited))

            # Global attributes
            elif key == 'attribute':
                for node in group:
                    name = node.attrib['name']
                    value = node.attrib['value']
                    nctype = node.attrib.get('type', 'String')
                    if nctype != 'String':
                        value = np.array([dtype[nctype](v)
                                          for v in value.split()])
                    nc.set_attribute(name, value)

            # Variables
            elif key == 'variable':
                for node in group:
                    shape = tuple(node.attrib['shape'].split())
                    var = Variable(ncstructure=nc,
                                   name=node.attrib['name'],
                                   nctype=node.attrib['type'],
                                   shape=shape)
                    nc.add_variable(var)
                    # Handle variable attributes, ignore values
                    for child in node:
                        if child.tag.split('}')[1] == 'attribute':
                            name = child.attrib['name']
                            value = child.attrib['value']
                            nctype = child.attrib.get('type', 'String')
                            if nctype != 'String':
                                value = np.array([dtype[nctype](v)
                                                  for v in value.split()])
                            var.set_attribute(name, value)

        return nc

    def write_CDL(self, fid):
        """Write Common Data Language

        Produce identical output as ncdump -h
        """
        ncname = os.path.basename(self.location)
        ncname = os.path.splitext(ncname)[0]  # Remove ".nc"
        fid.write('netcdf {} {{\n'.format(ncname))

        fid.write('dimensions:\n')
        for name, dim in self.dimensions.items():
            if dim.isUnlimited:
                fid.write('\t{} = UNLIMITED ; // ({} currently)\n'.
                          format(name, dim.length))
            else:
                fid.write('\t{} = {} ;\n'.format(name, dim.length))

        fid.write('variables:\n')
        for name, var in self.variables.items():
            fid.write('\t{} {}'.format(var.nctype, name))
            if len(var.shape) > 0:
                fid.write('(')
                for d in var.shape[:-1]:
                    fid.write('{}, '.format(d))
                fid.write('{}) ;\n'.format(var.shape[-1]))
            else:
                fid.write(' ;\n')

            for attname, att in var.attributes.items():
                if isinstance(att.value, string_type):
                    fid.write('\t\t{}:{} = "{}" ;\n'.
                              format(name, attname, att.value))
                else:
                    fid.write('\t\t{}:{} = {} ;\n'.
                              format(name, attname, vector2cdl(att.value)))

        if len(self.attributes) > 0:
            fid.write('\n// global attributes:\n')
            for attname, att in self.attributes.items():
                if isinstance(att.value, string_type):
                    fid.write('\t\t:{} = "{}" ;\n'.
                              format(attname, att.value))
                else:
                    fid.write('\t\t:{} = {} ;\n'.
                              format(attname, vector2cdl(att.value)))

        fid.write('}\n')

    def write_NcML(self, fid):
        fid.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        fid.write('<netcdf xmlns="http://www.unidata.ucar.edu/')
        fid.write('namespaces/netcdf/ncml-2.2"')
        # Determine wether location should include .nc
        location = self.location
        if not location.endswith('.nc'):
            location += '.nc'
        fid.write(' location="{}">\n'.format(location))

        # Dimensions
        for name, dim in self.dimensions.items():
            if dim.isUnlimited:
                fid.write('  <dimension name="{}" length="{}"'.
                          format(name, dim.length))
                fid.write(' isUnlimited="true" />\n')
            else:
                fid.write('  <dimension name="{}" length="{}" />\n'.
                          format(name, dim.length))

        # Global attributes
        for attname, att in self.attributes.items():
            fid.write('  <attribute name="{}" value="{}" />\n'.
                      format(attname, att.value))

        # Variables
        for name, var in self.variables.items():
            if len(var.shape) > 0:

                fid.write('  <variable name="{}" shape="{}" type="{}">\n'.
                          format(name, ' '.join(var.shape),  var.nctype))
            else:
                fid.write('  <variable name="{}" type="{}">\n'.
                          format(name, var.nctype))

            # Variable attributes
            for attname, att in var.attributes.items():
                attvalue = att.value
                if isinstance(attvalue, string_type):
                    fid.write('    <attribute name="{}" value="{}" />\n'.
                              format(attname, attvalue))
                else:
                    fid.write('    <attribute name=')
                    fid.write('"{}" type="{}" value="{}" />\n'.
                              format(attname, att.type,
                                     vector2ncml(att.value)))

            fid.write('  </variable>\n')

        fid.write('</netcdf>\n')


def isplit_noloss(predicate, iterator):
    """Splits an iterator where predicate fails

    Returns an iterator of lists
    Does not "loose" the boundary elements
    """

    accumulator = [next(iterator)]
    for x in iterator:
        if predicate(x):
            accumulator.append(x)
        else:
            yield (accumulator)
            accumulator = [x]
    yield (accumulator)  # Final part of the iterator


def parse_attribute(line):
    """Parse an attribute line from CDL, infer type"""
    words = line.split()
    words = [w.rstrip(',') for w in words]  # Strip trailing commas
    name = words[0].split(':')[1]
    values = words[2:-1]  # Between = and ;
    v0 = values[0]
    # text
    if v0.startswith('"'):
        value = line[line.index('"') + 1: line.rindex('"')]  # Between ""
    # short
    elif v0.endswith('s'):
        # nctype = 'short'
        value = np.array([int(v.rstrip('s')) for v in values],
                         dtype='int16')
    # float
    elif v0.endswith('f'):
        # nctype = 'float'
        value = np.array([float(v.rstrip('f')) for v in values],
                         dtype='float32')
    # double
    elif "." in v0:
        # nctype = 'double'
        value = np.array([float(v) for v in values],
                         dtype='float64')
    # integer
    else:  # integer
        # nctype = 'int'
        value = np.array([int(v) for v in values],
                         dtype='int32')
    # Make exception for bad entry
    return name, value


def vector2cdl(vector):
    """Make a CDL string representation of a numeric 1D array."""
    dtype = vector.dtype

    def normalize(x):
        if dtype == 'int16':
            s = '{}s'.format(x)
        elif dtype == 'int32':
            s = str(x)
        elif dtype == 'float32':
            s = str(x).rstrip('0')
            if '.' not in s:  # f.ex. s = 1e18
                s = s.replace('e', '.e')
            s = '{}f'.format(s)
        elif dtype == 'float64':
            s = str(x).rstrip('0')
            if '.' not in s:
                s = s.replace('e', '.e')
        else:
            print('Unknown type')
        return s  # end normalize

    return ', '.join(normalize(a) for a in vector)


def vector2ncml(vector):
    """Make a NcML string representation of a numeric 1D array."""
    dtype = vector.dtype

    def normalize(x):
        if dtype in ['int16', 'int32']:
            s = '{}'.format(x)
        elif dtype in ['float32', 'float64']:
            s = str(x).rstrip('0')  # 1.0 -> 1.
            if '.' not in s:  # 1e18 -> 1.e18
                s = s.replace('e', '.e')
            s = '{}'.format(s)
        else:
            print('Unknown type')
        return s  # end normalize

    return ' '.join(normalize(a) for a in vector)
