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
NCtype = {float   : 'double',
          int     : 'int',
          str     : 'char',
          'd'     : 'double',
          'f'     : 'float',
          'i'     : 'int',
          'h'     : 'short',
          'b'     : 'byte',
          'S'     : 'char',
          'U'     : 'char',
          }

# if PY2:
#    NCtype[unicode] = 'char'


class Dimension(object):
    """NetCDF dimensjon"""

    def __init__(self, name, size=None, isunlimited=False):
        self.name = name
        if size is None:
            self._size = 0
            self._isunlimited = True
        else:
            self._size = size
            self._isunlimited = isunlimited

    def __len__(self):
        return self._size

    def isunlimited(self):
        return self._isunlimited


class _Attribute(object):
    """NetCDF attribute"""

    def __init__(self, value):
        if isinstance(value, string_type):
            self.value = value
            self.type = 'char'   # Not used in NcML??
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
    def __init__(self, ncheader, name, nctype, dimensions=()):
        self.header = ncheader
        self.name = name
        self.nctype = nctype
        self.dimensions = dimensions
        self.shape = tuple([len(self.header.dimensions[d])
                            for d in self.dimensions])
        self.ndim = len(self.shape)
        _HasNCAttributes.__init__(self)

    def __len__(self):
        if self.shape:
            return self.shape[0]
        else:
            return 0   # Scalar variables, shape = ()


class NCheader(_HasNCAttributes):

    def __init__(self, location=None):
        self.location = location
        self.dimensions = OrderedDict()
        self.variables = OrderedDict()
        _HasNCAttributes.__init__(self)

    def add_dimension(self, dimension):
        self.dimensions.setdefault(dimension.name, dimension)

    def add_variable(self, variable):
        self.variables.setdefault(variable.name, variable)

    # ---

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
                v = Variable(ncheader=nc, name=name, nctype=var.nctype,
                             dimensions=var.dimensions)
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
    def from_CDL(self, filename):
        """Define the data structure from a CDL file"""
        fid = codecs.open(filename, encoding='utf-8')

        nc = NCheader()

        # Skip empty lines
        lines = (line for line in fid if line.split())

        # Location line
        words = next(lines).split()
        nc.location = words[1]

        # Dimensions
        next(lines)    # Skip "dimensions:"
        dimlines = it.takewhile(lambda x: x.split()[0] != 'variables:', lines)
        for line in dimlines:
            words = line.split()
            #print words
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
            if '(' in words[1]:   # has dimensions
                ndim = len(words) - 2
                name, dim0 = words[1].split('(')
                dims = [dim0]
                for i in range(1, ndim):
                    dims.append(words[i+1])
                dims[-1] = dims[-1][:-1]    # remove trailing ')'
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

    def write_CDL(self, fid):
        """Write Common Data Language

        Produce identical output as ncdump -h
        """
        ncname = os.path.basename(self.location)
        ncname = os.path.splitext(ncname)[0]   # Remove ".nc"
        fid.write('netcdf {} {{\n'.format(ncname))

        fid.write('dimensions:\n')
        for name, dim in self.dimensions.items():
            if dim.isunlimited():
                fid.write('\t{} = UNLIMITED ; // ({} currently)\n'.
                          format(name, len(dim)))
            else:
                fid.write('\t{} = {} ;\n'.format(name, len(dim)))

        fid.write('variables:\n')
        for name, var in self.variables.items():
            fid.write('\t{} {}'.format(var.nctype, name))
            if var.ndim > 0:
                fid.write('(')
                for d in var.dimensions[:-1]:
                    fid.write('{}, '.format(d))
                fid.write('{}) ;\n'.format(var.dimensions[-1]))
            else:
                fid.write(' ;\n')

            for attname, att in var.attributes.items():
                if isinstance(att.value, string_type):
                    fid.write('\t\t{}:{} = "{}" ;\n'.
                              format(name, attname, att.value))
                else:
                    fid.write('\t\t{}:{} = {} ;\n'.
                              format(name, attname, array2cdl(att.value)))

        if len(self.attributes) > 0:
            fid.write('\n// global attributes:\n')
            for attname, att in self.attributes.items():
                if isinstance(att.value, string_type):
                    fid.write('\t\t:{} = "{}" ;\n'.
                              format(attname, att.value))
                else:
                    fid.write('\t\t:{} = {} ;\n'.
                              format(attname, array2cdl(att.value)))

        fid.write('}\n')

    # ---

    # Må oppdateres, håndterer ikke type og array-attributter korrekt.
    def write_NcML(self, fid):
        fid.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        fid.write('<netcdf xmlns="http://www.unidata.ucar.edu/')
        fid.write('namespaces/netcdf/ncml-2.2"')
        fid.write(' location="{}">\n'.format(self.location))

        # Dimensions
        for name, dim in self.dimensions.items():
            if dim.isunlimited():
                fid.write('  <dimension name="{}" length="{}"'.
                          format(name, len(dim)))
                fid.write(' isUnlimited="true" />\n')
            else:
                fid.write('  <dimension name="{}" length="{}" />\n'.
                          format(name, len(dim)))

        # Global attributes
        for attname, att in nc.attributes.items():
            fid.write('  <attribute name="{}" value="{}" />\n'.
                      format(attname, att.value))

        # Variables
        for name, var in self.variables.items():
            if var.ndim > 0:
                fid.write('  <variable name="{}" shape="{}" type="{}">\n'.
                          format(name, ' '.join(var.dimensions),
                                 var.nctype))
            else:
                fid.write('  <variable name="{}" type="{}">\n'.
                          format(name, var.nctype))

            # Variable attributes
            for attname, att in var.attributes.items():
                attvalue = att.value
                if isinstance(attvalue, string_type):
                    fid.write('    <attribute name="{}" value="{}" />\n'.
                              format(attname, attvalue))
                else:  #NOTE: how to find type
                    string = str(attvalue)
                    if string[-2:] == ".0":
                        string = string[:-1]
                    fid.write('    <attribute name=')
                    fid.write('"{}" type="double" value="{}" />\n'.
                              format(attname, string))

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
            yield(accumulator)
            accumulator = [x]
    yield(accumulator)         # Final part of the iterator


def parse_attribute(line):
    """Parse an attribute line from CDL, infer type"""
    words = line.split()
    words = [w.rstrip(',') for w in words]  # Strip trailing commas
    name = words[0].split(':')[1]
    values = words[2:-1]   # Between = and ;
    v0 = values[0]
    # text
    if v0.startswith('"'):
        value = line[line.index('"')+1: line.rindex('"')]   # Between ""
    # short
    elif v0.endswith('s'):
        #nctype = 'short'
        value = np.array([int(v.rstrip('s')) for v in values],
                         dtype='int16')
    # float
    elif v0.endswith('f'):
        #nctype = 'float'
        value = np.array([float(v.rstrip('f')) for v in values],
                         dtype='float32')
    # double
    elif "." in v0:
        #nctype = 'double'
        value = np.array([float(v) for v in values],
                         dtype='float64')
    # integer
    else:   # integer
        #nctype = 'int'
        value = np.array([int(v) for v in values],
                         dtype='int32')
    # Make exception for bad entry
    # print name, nctype, value
    return name, value


def array2cdl(A):
    """Make a CDL string representation of a numeric 1D array."""
    dtype = A.dtype

    def normalize(a):
        if dtype == 'int16':
            s = '{}s'.format(a)
        elif dtype == 'int32':
            s = str(a)
        elif dtype == 'float32':
            s = str(a).rstrip('0')
            if '.' not in s:  # f.ex. s = 1e18
                s = s.replace('e', '.e')
            s = '{}f'.format(s)
        elif dtype == 'float64':
            s = str(a).rstrip('0')
            if '.' not in s:
                s = s.replace('e', '.e')
        else:
            print('Unknown type')
            print(a)
        return s  # end normalize
    return ', '.join(normalize(a) for a in A)


# ====================================

if __name__ == '__main__':
    ncfile = '/home/bjorn/python/roms-python-tutorial/data/ocean_avg_0014.nc'
    #ncfile = 'b.nc'
    #nc = NCheader.from_file(ncfile)
    #v = nc.variables['temp']
    #nc.write_CDL()
    #nc.write_NcML(sys.stdout)
    nc = NCheader.from_CDL('test.cdl')
    #nc.write_CDL(sys.stdout)
    nc.write_NcML(sys.stdout)
