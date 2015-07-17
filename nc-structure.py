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

import numpy as np
from netCDF4 import Dataset

# Mapping from dtype.char or python type to NetCDF type
NCtype = {float               : 'double',
          'd'                 : 'double',
          #np.float64          : 'double',
          #np.dtype('float64') : 'double',
          #np.float32          : 'float',
          'f'                 : 'float',
          #np.dtype('float32') : 'float',
          int                 : 'int',
          'i'                 : 'int',
          #np.int32            : 'int',
          #np.dtype('int32')   : 'int',
          #np.int16            : 'short',
          'h'                 : 'short',
          np.dtype('int16')   : 'short',
          #np.int8             : 'byte',
          'b'                 : 'byte',
          #np.dtype('int8')    : 'byte',
          str                 : 'char',
          unicode             : 'char',
          #np.dtype('S1')      : 'char',
          'S'                 : 'char',
          'U'                 : 'char',
}
          

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

    def __init__(self, value, type=None):
        #self.name = name
        self.value = value
        self.type = type
        if type is None:
            self.type = NCtype[np.asarray(value).dtype.char]


class _HasNCAttributes(object):

    # Open for kwargs
    def __init__(self):
        self.attributes = OrderedDict()

    def set_attribute(self, key, value, dtype=None):
        self.attributes[key] = _Attribute(value, dtype)

    # Hva om attribute ikke finnes?
    def delete_attribute(self, key):
        del self[key]

    def ncattrs(self):
        return self.attributes.keys()


class Variable(_HasNCAttributes):
    """NetCDF variable"""

    # Ta attributter som ekstra argumenter
    def __init__(self, ncheader, name, dtype, dimensions=()):
        self.header = ncheader
        self.name = name
        self.dtype = dtype
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

            for name, dim in fid.dimensions.iteritems():
                d = Dimension(name, len(dim), dim.isunlimited())
                nc.add_dimension(d)

            for name, var in fid.variables.iteritems():
                # Slå sammen til createVariable
                v = Variable(ncheader=nc, name=name, dtype=var.dtype.char,
                             dimensions=var.dimensions)
                nc.add_variable(v)
                # Variable attributes
                for att in var.ncattrs():
                    v.set_attribute(att, getattr(var, att))

            # Global attributes
            for att in fid.ncattrs():
                nc.set_attribute(att, getattr(fid, att))

        return nc

    # ---

    def write_CDL(self, fid=sys.stdout):
        """Write Common Data Language

        Produce identical output as ncdump -h
        """
        ncname = os.path.basename(self.location)
        ncname = os.path.splitext(ncname)[0]   # Remove ".nc"
        fid.write('netcdf {} {{\n'.format(ncname))

        fid.write('dimensions:\n')
        for name, dim in self.dimensions.iteritems():
            if dim.isunlimited():
                fid.write('\t{} = UNLIMITED ; // ({} currently)\n'.
                          format(name, len(dim)))
            else:
                fid.write('\t{} = {} ;\n'.format(name, len(dim)))

        fid.write('variables:\n')
        for name, var in self.variables.iteritems():
            fid.write('\t{} {}'.format(NCtype[var.dtype], name))
            if var.ndim > 0:
                fid.write('(')
                for d in var.dimensions[:-1]:
                    fid.write('{}, '.format(d))
                fid.write('{}) ;\n'.format(var.dimensions[-1]))
            else:
                fid.write(' ;\n')

            for attname, attvalue in var.attributes.iteritems():
                if isinstance(attvalue, basestring):
                    fid.write('\t\t{}:{} = "{}" ;\n'.
                              format(name, attname, attvalue))
                else:
                    string = str(attvalue)
                    if string[-2:] == ".0":
                        string = string[:-1]
                    fid.write('\t\t{}:{} = {} ;\n'.
                              format(name, attname, string))

        fid.write('\n// global attributes:\n')
        for attname, attvalue in nc.attributes.iteritems():
            if isinstance(attvalue, basestring):
                fid.write('\t\t:{} = "{}" ;\n'.
                          format(attname, attvalue))
            else:
                string = str(attvalue)
                if string[:-2] == ".0":
                    string = string[:-1]
                fid.write('\t\t:{} = {} ;\n'.format(attname, string))

        fid.write('}\n')
 
    # ---  

    def write_NcML(self, fid):
        fid.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        fid.write('<netcdf xmlns="http://www.unidata.ucar.edu/')
        fid.write('namespaces/netcdf/ncml-2.2"')
        fid.write(' location="{}">\n'.format(self.location))

        # Dimensions
        for name, dim in self.dimensions.iteritems():
            if dim.isunlimited():
                fid.write('  <dimension name="{}" length="{}"'.
                          format(name, len(dim)))
                fid.write(' isUnlimited="true" />\n')
            else:
                fid.write('  <dimension name="{}" length="{}" />\n'.
                          format(name, len(dim)))
                
        # Global attributes
        for attname, att in nc.attributes.iteritems():
            fid.write('  <attribute name="{}" value="{}" />\n'.
                      format(attname, att.value))

        # Variables
        for name, var in self.variables.iteritems():
            if var.ndim > 0:
                fid.write('  <variable name="{}" shape="{}" type="{}">\n'.
                          format(name, ' '.join(var.dimensions),
                                 NCtype[var.dtype]))
            else:
                fid.write('  <variable name="{}" type="{}">\n'.
                          format(name, NCtype[var.dtype]))

            # Variable attributes
            for attname, att in var.attributes.iteritems():
                attvalue = att.value
                if isinstance(attvalue, basestring):
                    fid.write('    <attribute name="{}" value="{}" />\n'.
                              format(attname, attvalue))
                else:  #NOTE: how to find type
                    string = str(attvalue)
                    if string[-2:] == ".0":
                        string = string[:-1]
                    fid.write('    <attribute name="{}" type="double" value="{}" />\n'.
                              format(attname, string))

            fid.write('  </variable>\n')

        fid.write('</netcdf>\n')

# ====================================

if __name__ == '__main__':
    import sys
    ncfile = '/home/bjorn/python/roms-python-tutorial/data/ocean_avg_0014.nc'
    #ncfile = 'b.nc'
    nc = NCheader.from_file(ncfile)
    #v = nc.variables['temp']
    #nc.write_CDL()
    nc.write_NcML(sys.stdout)

