# -*- coding: utf-8 -*-

# Bør teste på CDl fil med variable
# sjekke at de ignoreres

import codecs
import itertools
from collections import OrderedDict

import numpy as np

#from ncstructure import parse_attribute


# sjekk litt opp, hva som godtas av tekst
nctypes = ['short', 'int', 'long', 'float', 'double']

def logical_lines(lines):
    
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
        if line[-1] in [';', '{', ':']:
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
    line = line.replace('(', ' ')
    line = line.replace(')', ' ')
    words = line.split()
    nctype = words[0]
    name = words[1]
    shape = tuple(words[2:])
    return nctype, name, shape


def parse_attribute(line):

    """Parse an attribute line from CDL, infer type"""

    if line.lstrip()[0] == ':':
        var = None
    else:
        var = True

    line = line.replace(':', ' ')
    line = line.replace('=', ' ')
    words = line.split()

    if var:
        var = words[0]
        words[0:1] = []
    
    words = [w.rstrip(',') for w in words]  # Strip trailing commas

#    print words

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

    with codecs.open(cdl_file, encoding='utf-8') as fid:
    
        # Remove data lines, anything after "data:"
        lines = itertools.takewhile(lambda x: not x.lstrip().startswith('data:'), fid)

        lines = logical_lines(lines)

        print "--> location = ", next(lines).split()[1]  # netcdf <location> {

        att_lines = []
        dim_lines = []
        var_lines = []

        
        for line in lines:

            if ':' in line:
                att_lines.append(line)

            elif '=' in line:
                dim_lines.append(line)

            else:
                words = line.split()
                if words[0] in nctypes:
                    var_lines.append(line)

        return dim_lines, var_lines, att_lines

if __name__ == '__main__':
        
    dim_lines, var_lines, att_lines = parse_CDL("a.cdl")
        

    print "--> dimensions"
    for line in dim_lines:
        print parse_dimension(line)

    var_att = dict()
    var_att[None] = []
    variables = [parse_variable(line) for line in var_lines]
    # Prøv dict-comprehension
    for var in variables:
        var_att[var[1]] = []

    for line in att_lines:
        a = parse_attribute(line)
        var_att[a[0]].append(a[1:])

    # Print variables with attributes
    print "--> variables"    
    for line in var_lines:
        v = parse_variable(line)
        print v
        for att in var_att[v[1]]:
            print "   ", att

    # print global attribures
    print "--> Global attributes"        
    for att in var_att[None]:
        print att



        
    
