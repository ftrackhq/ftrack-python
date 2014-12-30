# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack


class Symbol(object):
    '''A constant symbol.'''

    def __init__(self, name):
        '''Initialise symbol with unique *name*.'''
        self.name = name

    def __str__(self):
        '''Return string representation.'''
        return self.name

    def __repr__(self):
        '''Return representation.'''
        return '{0}({1})'.format(self.__class__.__name__, self.name)


#: Symbol representing that no value has been set or loaded.
NOT_SET = Symbol('NOT_SET')
