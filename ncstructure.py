# -*- coding: utf-8 -*-

"""
ncstructure:

Class for structure of a classic netCDF file

"""

# --- Imports ---

from __future__ import unicode_literals, print_function

import sys
import os
from operator import attrgetter
from collections import OrderedDict
import itertools as it
import codecs
from xml.etree import ElementTree

import numpy as np
from netCDF4 import Dataset

from parse_CDL import parse_CDL

# --- Python2/3 ---

PY2 = sys.version_info[0] == 2
# PY3 = sys.version_info[0] == 3

# Ensure stdout is OK
if PY2:
    sys.stdout = codecs.getwriter('utf8')(sys.stdout)

# Follow six convention
string_type = str  # python 3
if PY2:
    string_type = basestring


# --- Conversion dictionaries ---

# Conversion from numpy dtype.char to NetCDF type
# May change to l -> long (not supported in NetCDF 3)
NCtype = dict(h='short', i='int', l='int', f='float', d='double', S='String')

# Conversion from nctype to numpy dtype
Dtype = dict(short=np.int16, int=np.int32, float=np.float32, double=np.float64)

# --- Main class ---


class NCstructure(object):
    """NetCDF structure"""

    class Dimension(object):
        """NetCDF dimension"""

        def __init__(self, name, length, isUnlimited=False):
            self._name = name
            self.length = length
            self.isUnlimited = isUnlimited

        name = property(attrgetter('_name'))

        # Compatibility functions with netcdf4-python
        def __len__(self):
            return self.length

        def isunlimited(self):
            return self.isUnlimited

    class Attribute(object):
        """NetCDF attribute"""

        def __init__(self, name, value):
            self._name = name
            if isinstance(value, string_type):
                self.nctype = 'String'
                self.value = value
            else:
                self.value = np.atleast_1d(value)
                self.nctype = NCtype[np.asarray(value).dtype.char]

        name = property(attrgetter('_name'))

    class Variable(object):
        """NetCDF variable"""

        def __init__(self, name, nctype, shape=()):
            self._name = name
            self.nctype = nctype
            self.shape = tuple(shape)
            self.attributes = OrderedDict()

        name = property(attrgetter('_name'))

        def createAttribute(self, name, value):
            """Set a NetCDF variable attribute"""
            self.attributes[name] = NCstructure.Attribute(name, value)

        def renameAttribute(self, oldname, newname):
            att = self.attributes[oldname]
            att._name = newname
            replace_ordered_key(self.attributes, oldname, newname)

    # NCstructure.__init__
    def __init__(self, location=None):
        self.location = location
        self.dimensions = OrderedDict()
        self.variables = OrderedDict()
        self.attributes = OrderedDict()

    def createDimension(self, name, length=None, isUnlimited=False):
        """Define a dimension in the structure"""
        if length is None:
            unlim = True
            len_ = 0
        else:
            unlim = isUnlimited

            len_ = length
        dim = self.Dimension(name, len_, unlim)
        self.dimensions[name] = dim
        return dim

    def createAttribute(self, name, value):
        """Set a netCDF global attribute"""
        self.attributes[name] = NCstructure.Attribute(name, value)

    def createVariable(self, name, nctype, shape):
        """Define a netCDF variable in the structure"""
        # Sanity check
        for d in shape:
            assert d in self.dimensions.keys()
        var = self.Variable(name, nctype, shape)
        self.variables[name] = var
        return var

    def renameDimension(self, oldname, newname):
        dim = self.dimensions[oldname]
        dim._name = newname
        # rename the key of the OrderedDict in place
        replace_ordered_key(self.dimensions, oldname, newname)
        # rename the variable shapes
        for varname, var in self.variables.items():
            if oldname in var.shape:
                L = list(var.shape)
                L[L.index(oldname)] = newname
                var.shape = tuple(L)

    def renameVariable(self, oldname, newname):
        var = self.variables[oldname]
        var._name = newname
        replace_ordered_key(self.variables, oldname, newname)

    def renameAttribute(self, oldname, newname):
        att = self.attributes[oldname]
        att._name = newname
        replace_ordered_key(self.attributes, oldname, newname)

    @classmethod
    def from_file(cls, filename):
        """Extract the structure from a netCDF file"""

        with Dataset(filename) as fid:
            nc = cls(location=filename)

            for name, dim in fid.dimensions.items():
                nc.createDimension(name, len(dim), dim.isunlimited())

            for name, var in fid.variables.items():
                nctype = NCtype[var.dtype.char]
                v = nc.createVariable(name, nctype, shape=var.dimensions)

                # Variable attributes
                for att in var.ncattrs():
                    v.createAttribute(att, getattr(var, att))

            # Global attributes
            for att in fid.ncattrs():
                nc.createAttribute(att, getattr(fid, att))

        return nc

    @classmethod
    def from_CDL(cls, filename):
        """Extract the structure from a CDL file"""

        location, dimensions, variables, attributes = parse_CDL(filename)

        nc = NCstructure(location)

        for dim in dimensions:
            nc.createDimension(*dim)

        for var in variables:
            v = nc.createVariable(*var)
            for att in attributes[var[0]]:
                v.createAttribute(att[1], att[2])

        for att in attributes[None]:
            nc.createAttribute(att[1], att[2])

        return nc

    @classmethod
    def from_NcML(cls, filename):
        """Extract the structure from a NcML file"""

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
                    nc.createDimension(name, length, isunlimited)

            # Global attributes
            elif key == 'attribute':
                for node in group:
                    name = node.attrib['name']
                    value = node.attrib['value']
                    nctype = node.attrib.get('type', 'String')
                    if nctype != 'String':
                        value = np.array([Dtype[nctype](v)
                                          for v in value.split()])
                    nc.createAttribute(name, value)

            # Variables
            elif key == 'variable':
                for node in group:
                    shape = tuple(node.attrib['shape'].split())
                    var = nc.createVariable(node.attrib['name'],
                                            node.attrib['type'], shape)
                    # Handle variable attributes, ignore values
                    for child in node:
                        if child.tag.split('}')[1] == 'attribute':
                            name = child.attrib['name']
                            value = child.attrib['value']
                            nctype = child.attrib.get('type', 'String')
                            if nctype != 'String':
                                value = np.array([Dtype[nctype](v)
                                                  for v in value.split()])
                            var.createAttribute(name, value)

        return nc

    def write_CDL(self, fid=sys.stdout):
        """Write Common Data Language

        Produce identical output as ncdump -h
        """
        ncname = os.path.basename(self.location)
        ncname = os.path.splitext(ncname)[0]  # Remove ".nc"
        fid.write('netcdf {} {{\n'.format(ncname))

        if self.dimensions:
            fid.write('dimensions:\n')
        for name, dim in self.dimensions.items():
            if dim.isUnlimited:
                fid.write('\t{} = UNLIMITED ; // ({} currently)\n'.
                          format(name, dim.length))
            else:
                fid.write('\t{} = {} ;\n'.format(name, dim.length))

        if self.variables:
            fid.write('variables:\n')
        for varname, var in self.variables.items():
            fid.write('\t{} {}'.format(var.nctype, varname))
            if var.shape:
                fid.write('(')
                for d in var.shape[:-1]:
                    fid.write('{}, '.format(d))
                fid.write('{}) ;\n'.format(var.shape[-1]))
            else:
                fid.write(' ;\n')

            for attname, att in var.attributes.items():
                if isinstance(att.value, string_type):
                    fid.write('\t\t{}:{} = "{}" ;\n'.
                              format(varname, attname, att.value))
                else:
                    fid.write('\t\t{}:{} = {} ;\n'.
                              format(varname, attname, vector2cdl(att.value)))

        if self.attributes:
            fid.write('\n// global attributes:\n')
            for attname, att in self.attributes.items():
                if isinstance(att.value, string_type):
                    fid.write('\t\t:{} = "{}" ;\n'.
                              format(attname, att.value))
                else:
                    fid.write('\t\t:{} = {} ;\n'.
                              format(attname, vector2cdl(att.value)))

        fid.write('}\n')

    def write_NcML(self, fid=sys.stdout):
        """Write the structure to a NcML file"""

        fid.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        fid.write('<netcdf xmlns="http://www.unidata.ucar.edu/')
        fid.write('namespaces/netcdf/ncml-2.2"')
        # Determine whether location should include .nc
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
        for varname, var in self.variables.items():
            if var.shape:
                fid.write('  <variable name="{}" shape="{}" type="{}">\n'.
                          format(varname, ' '.join(var.shape), var.nctype))
            else:
                fid.write('  <variable name="{}" type="{}">\n'.
                          format(varname, var.nctype))

            # Variable attributes
            for attname, att in var.attributes.items():
                attvalue = att.value
                if isinstance(attvalue, string_type):
                    fid.write('    <attribute name="{}" value="{}" />\n'.
                              format(attname, attvalue))
                else:
                    fid.write('    <attribute name=')
                    fid.write('"{}" type="{}" value="{}" />\n'.
                              format(attname, att.nctype,
                                     vector2ncml(att.value)))

            fid.write('  </variable>\n')

        fid.write('</netcdf>\n')

# --- utility functions ---


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
            yield accumulator
            accumulator = [x]
    yield accumulator  # Final part of the iterator


def vector2cdl(vector):
    """Make a CDL string representation of a numeric 1D array."""
    dtype = vector.dtype

    def normalize(x):
        """Normalize a single value for CDL"""
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
        """Normalize a single value for NcML"""

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


def replace_ordered_key(D, oldkey, newkey):
    """Replace a key in-place in an OrderedDict"""
    # Rotate the items, replacing the actual key
    # From fbstj at stackoverflow
    for i in range(len(D)):
        key, value = D.popitem(False)
        if key == oldkey:
            key = newkey
        D[key] = value
