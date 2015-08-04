# Can only create Dimension objects when you are in Struc!

class Struc(object):

    class Dimension(object):

        def __init__(self, length):
            self.length = length

    class Variable(object):

        def __init__(self, type, shape):
            self.type = type
            self.shape = shape
            self.attributes = dict()
            
        def createAttribute(self, name, value):
            att = self.Attribute(value)
            self.attributes[name] = att

    class Attribute(object):
        def __init__(self, value, type=None):
            self.value = value
            self.type = 'String' # har logikk for dette

    def __init__(self):
        self.dimensions = dict()
        self.variables = dict()

    def createDimension(self, name, length):
        dim = self.Dimension(length)
        self.dimensions[name] = dim

    def createVariable(self, name, type, shape):
        # Sanity check
        for d in shape:
            assert d in self.dimensions.keys()
        var = self.Variable(type, shape)
        self.variables[name] = var
        
        
s = Struc()

s.createDimension('X', 10)

s.createVariable('temp', 'float', ('X',))



    
