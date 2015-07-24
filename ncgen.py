# -*- coding: utf-8 -*-

"""Make a python function defining a given netcdf structure"""

from __future__ import unicode_literals

from netCDF4 import Dataset
from ncstructure import NCheader

# Translate netCDF types to netcdf4-python types
fixtype = dict(short='i2', int='i', float='f', double='d', char='c')


def ncgen(nc, f):
    """Generate a script defining the netcdf structure"""

    # --- Header stuff

    f.write('# -*- coding: utf-8 -*-\n')
    f.write('\nfrom __future__ import unicode_literals\n\n')
    f.write('import numpy as np\n')
    f.write('from netCDF4 import Dataset\n')
    f.write('\n\n')

    # --- Function

    f.write("def defineCDF():\n")
    f.write('    """Create/define a netCDF file with given structure"""\n')
    f.write("\n    # --- Create netCDF file\n")
    f.write("    ncid = Dataset('{}.nc', mode='w', ".format(nc.location))
    f.write("format='NETCDF3_CLASSIC')\n")

    # --- Dimension

    if len(nc.dimensions) > 0:
        f.write("\n    # --- Dimensions\n")
    for name in nc.dimensions:
        dim = nc.dimensions[name]
        if dim.isunlimited():
            length = 'None'
        else:
            length = len(dim)
        f.write("    ncid.createDimension('{}', {})\n".format(name, length))

    # TODO:  Har ikke lagt inn håndtering av _FillValue

    # --- Variables

    if len(nc.variables) > 0:
        f.write("\n    # --- Variables\n")
    for name in nc.variables:
        var = nc.variables[name]
        f.write("    v = ncid.createVariable('{}', '{}', {})\n".
                format(name, fixtype[var.nctype], str(var.dimensions)))
        for name in var.attributes:
            value = var.attributes[name].value
            if isinstance(value, basestring):
                value = "'{}'".format(value)
            else:
                value = 'np.' + repr(value).replace('dtype=', 'dtype=np.')
            f.write("    v.{} = {}\n".format(name, value))

    # --- Global attributes

    if len(nc.attributes) > 0:
        f.write("\n    # --- Global attributes\n")
    for name in nc.attributes:
        value = nc.attributes[name].value
        if isinstance(value, basestring):
            value = "'{}'".format(value)
        else:
            value = 'np.' + repr(value).replace('dtype=', 'dtype=np.')
        f.write("    ncid.{} = {}\n".format(name, value))

    f.write("\n    return ncid\n")

    # --- Main
    f.write("\nif __name__ == '__main__':\n")
    f.write("    ncid = defineCDF()\n")
    f.write("    ncid.close()\n")

if __name__ == '__main__':

    import sys
    nc = NCheader.from_CDL('test.cdl')

    fid = sys.stdout
    ncgen(nc, fid)

    fid.write('\nncid.close()\n')
