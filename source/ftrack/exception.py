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


class NotFoundError(Error):
    '''Raise when something that should exist is not found.'''

    defaultMessage = 'Not found.'


class NotUniqueError(Error):
    '''Raise when unique value required and duplicate detected.'''

    defaultMessage = 'Non-unique value detected.'


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


class InvalidStateError(Error):
    '''Raise when an invalid state detected.'''

    defaultMessage = 'Invalid state.'


class InvalidStateTransitionError(InvalidStateError):
    '''Raise when an invalid state transition detected.'''

    def __init__(self, current_state, target_state, entity, **kw):
        '''Initialise error.'''
        self.current_state = current_state
        self.target_state = target_state
        self.entity = entity
        super(InvalidStateTransitionError, self).__init__(**kw)

    defaultMessage = (
        'Invalid transition from {current_state!r} to {target_state!r} state '
        'for entity {entity!r}'
    )


class AttributeError(Error):
    '''Raise when an error related to an attribute occurs.'''

    defaultMessage = 'Attribute error.'


class ImmutableAttributeError(AttributeError):
    '''Raise when modification of immutable attribute attempted.'''

    def __init__(self, attribute, **kw):
        '''Initialise error.'''
        self.attribute = attribute
        super(ImmutableAttributeError, self).__init__(**kw)

    defaultMessage = (
        'Cannot modify value of immutable {attribute.name!r} attribute.'
    )


class CollectionError(Error):
    '''Raise when an error related to collections occurs.'''

    defaultMessage = 'Collection error.'

    def __init__(self, collection, **kw):
        '''Initialise error.'''
        self.collection = collection
        super(CollectionError, self).__init__(**kw)


class ImmutableCollectionError(CollectionError):
    '''Raise when modification of immutable collection attempted.'''

    defaultMessage = (
        'Cannot modify value of immutable collection {collection!r}.'
    )


class DuplicateItemInCollectionError(CollectionError):
    '''Raise when duplicate item in collection detected.'''

    def __init__(self, item, collection, **kw):
        '''Initialise error.'''
        self.item = item
        super(DuplicateItemInCollectionError, self).__init__(collection, **kw)

    defaultMessage = (
        'Item {item!r} already exists in collection {collection!r}.'
    )


class ParseError(Error):
    '''Raise when a parsing error occurs.'''

    defaultMessage = 'Failed to parse.'


class EventHubError(Error):
    '''Raise when issues related to event hub occur.'''

    defaultMessage = 'Event hub error occurred.'


class EventHubConnectionError(EventHubError):
    '''Raise when event hub encounters connection problem.'''

    defaultMessage = 'Event hub is not connected.'


class EventHubPacketError(EventHubError):
    '''Raise when event hub encounters an issue with a packet.'''

    defaultMessage = 'Invalid packet.'
