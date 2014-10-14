# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import sys
import traceback


class Error(Exception):
    '''ftrack specific error.'''

    defaultMessage = 'Unspecified error occurred.'

    def __init__(self, message=None, details=None, **kw):
        '''Initialise exception with *message*.

        If *message* is None, the class 'defaultMessage' will be used.

        '''
        if message is None:
            message = self.defaultMessage

        self.message = message
        self.details = details
        self.traceback = traceback.format_exc()

    def __str__(self):
        '''Return string representation.'''
        keys = {}
        for key, value in self.__dict__.iteritems():
            if isinstance(value, unicode):
                value = value.encode(sys.getfilesystemencoding())
            keys[key] = value

        return str(self.message.format(**keys))


class AuthenticationError(Error):
    '''Raise when an authentication error occurs.'''

    defaultMessage = 'Authentication error.'


class ServerError(Error):
    '''Raise when the server reports an error.'''

    defaultMessage = 'Server reported error processing request.'


class NotUniqueError(Error):
    '''Raise when unique value required and duplicate detected.'''

    defaultMessage = 'Configuration error.'


class EntityTypeError(Error):
    '''Raise when an entity type error occurs.'''

    defaultMessage = 'Entity type error.'


class UnrecognisedEntityTypeError(EntityTypeError):
    '''Raise when an unrecognised entity type detected.'''

    def __init__(self, entity_type, **kw):
        '''Initialise with *entity_type* that is unrecognised.'''
        self.entity_type = entity_type
        super(UnrecognisedEntityTypeError, self).__init__(**kw)

    defaultMessage = 'Entity type "{entity_type}" not recognised.'


class InvalidState(Error):
    '''Raise when an invalid state detected.'''

    defaultMessage = 'Invalid state.'


class InvalidStateTransition(InvalidState):
    '''Raise when an invalid state transition detected.'''

    def __init__(self, current_state, target_state, entity, **kw):
        '''Initialise error.'''
        self.current_state = current_state
        self.target_state = target_state
        self.entity = entity
        super(InvalidStateTransition, self).__init__(**kw)

    defaultMessage = (
        'Invalid transition from {current_state!r} to {target_state!r} state '
        'for entity {entity!r}'
    )
