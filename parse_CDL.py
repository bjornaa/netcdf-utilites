# -*- coding: utf-8 -*-

"""A parser for Common Data Language"""

from __future__ import print_function

import codecs
import itertools

import numpy as np

# Must add something on text types
nctypes = ['short', 'int', 'long', 'float', 'double']


def logical_lines(lines):
    """Iterator of logical lines in a CDL file"""

    # Strip line-shifts and trailing blanks
    lines = (line.rstrip() for line in lines)

    # Remove comments
    lines = (line.split('//')[0] for line in lines)

    # Ignore empty lines
    lines = (line for line in lines if line)

    # Use logical lines
    lines = split_lines(join_lines(lines))

    return lines


def join_lines(lines):
    """Make an iterator of logical lines from an iterator of lines"""
    joined_line = []
    for line in lines:
        if line[-1] in [';', '{', ':']:   # End symbols for logical lines
            joined_line.append(line[:-1])
            yield ' '.join(joined_line)
            joined_line = []
        else:
            joined_line.append(line)


def split_lines(lines):
    """Split lines at ';' """
    for line in lines:
        sublines = line.split(';')
        for subline in sublines:
            yield subline


def parse_dimension(line):
    """Parse a dimension line from CDL"""
    line = line.replace('=', ' ')
    words = line.split()
    name = words[0]
    if words[1].upper() == "UNLIMITED":
        length = 0
        isUnlimited = True
    else:
        length = int(words[1])
        isUnlimited = False
    return name, length, isUnlimited


def parse_variable(line):
    """Parse a variable line from CDL"""
    line = line.replace('(', ' ')
    line = line.replace(')', ' ')
    line = line.replace(',', ' ')
    words = line.split()
    nctype = words[0]
    name = words[1]
    shape = tuple(words[2:])
    return nctype, name, shape


def parse_attribute(line):
    """Parse an attribute line from CDL, infer type"""

    if line.lstrip()[0] == ':':  # Global attribute
        var = None
    else:                        # Variable attribute
        var = True

    # Split the line
    line = line.replace(':', ' ')
    line = line.replace('=', ' ')
    words = line.split()
    if var:
        var = words[0]
        words[0:1] = []

    words = [w.rstrip(',') for w in words]  # Strip trailing commas

    name = words[0]
    values = words[1:]  # Between = and ;
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
    return var, name, value


def parse_CDL(cdl_file):

    # Open the file
    with codecs.open(cdl_file, encoding='utf-8') as fid:

        # Remove data lines, anything after "data:"
        lines = itertools.takewhile(lambda x:
                                    not x.lstrip().startswith('data:'), fid)

        # Consider logical lines
        lines = logical_lines(lines)

        location = next(lines).split()[1]  # netcdf <location- {

        # Accumulators
        att_lines = []
        dim_lines = []
        var_lines = []

        for line in lines:

            # Attribute lines
            if ':' in line:
                att_lines.append(line)

            # Dimension lines
            elif '=' in line:
                dim_lines.append(line)

            # Variable lines
            else:
                words = line.split()
                if words[0] in nctypes:
                    var_lines.append(line)

            # Parse the lines
            dimensions = [parse_dimension(line) for line in dim_lines]
            variables = [parse_variable(line) for line in var_lines]
            attributes = {var[1]: [] for var in variables}
            attributes[None] = []   # Global attributes
            for line in att_lines:
                att = parse_attribute(line)
                attributes[att[0]].append(att)

        return location, dimensions, variables, attributes

if __name__ == '__main__':

    location, dimensions, variables, attributes = parse_CDL("a.cdl")

    print("--- Location: ", location)
    print("\n--- Dimensions:")
    for dim in dimensions:
        print(dim)

    # Print variables with attributes
    print("\n--- Variables")
    for var in variables:
        print(var)
        for att in attributes[var[1]]:
            print("   ", att[1:])

    # print global attribures
    print("\n--- Global attributes:")
    for att in attributes[None]:
        print(att[1:])
