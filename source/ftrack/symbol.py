# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack


class Symbol(object):
    '''A constant symbol.'''

    def __init__(self, name, value=True):
        '''Initialise symbol with unique *name* and *value*.

        *value* is used for nonzero testing.

        '''
        self.name = name
        self.value = value

    def __str__(self):
        '''Return string representation.'''
        return self.name

    def __repr__(self):
        '''Return representation.'''
        return '{0}({1})'.format(self.__class__.__name__, self.name)

    def __nonzero__(self):
        '''Return whether symbol represents non-zero value.'''
        return bool(self.value)


#: Symbol representing that no value has been set or loaded.
NOT_SET = Symbol('NOT_SET', False)
