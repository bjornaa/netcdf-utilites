# -*- coding: utf-8 -*-

"""Make a python function defining a given netcdf structure"""

from __future__ import unicode_literals

from ncstructure import NCstructure

# Translate netCDF types to netcdf4-python types
type_abbrev = dict(short='i2', int='i', float='f', double='d', char='c')


def ncgen(ncstruc, f):
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
    f.write("    ncid = Dataset('{}.nc', mode='w', ".format(ncstruc.location))
    f.write("format='NETCDF3_CLASSIC')\n")

    # --- Dimension

    if len(ncstruc.dimensions) > 0:
        f.write("\n    # --- Dimensions\n")
    for name in ncstruc.dimensions:
        dim = ncstruc.dimensions[name]
        if dim.isunlimited():
            length = 'None'
        else:
            length = len(dim)
        f.write("    ncid.createDimension('{}', {})\n".format(name, length))

    # TODO:  Har ikke lagt inn håndtering av _FillValue

    # --- Variables

    if len(ncstruc.variables) > 0:
        f.write("\n    # --- Variables\n")
    for name in ncstruc.variables:
        var = ncstruc.variables[name]
        attributes = var.attributes
        if '_FillValue' in attributes:
            f.write("    v = ncid.createVariable('{}', '{}', {}".
                    format(name, type_abbrev[var.nctype], str(var.dimensions)))
            f.write(", fill_value={})\n".format(attributes['_FillValue'].value[0]))
            attributes.pop('_FillValue')
        else:
            f.write("    v = ncid.createVariable('{}', '{}', {}\n".
                    format(name, type_abbrev[var.nctype], str(var.dimensions)))
        for attname in attributes:
            value = var.attributes[attname].value
            if isinstance(value, basestring):
                value = "'{}'".format(value)
            else:
                value = 'np.' + repr(value).replace('dtype=', 'dtype=np.')
            f.write("    v.{} = {}\n".format(attname, value))

    # --- Global attributes

    if len(ncstruc.attributes) > 0:
        f.write("\n    # --- Global attributes\n")
    for name in ncstruc.attributes:
        value = ncstruc.attributes[name].value
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

    nc = NCstructure.from_CDL('test.cdl')

    fid = sys.stdout
    ncgen(nc, fid)
