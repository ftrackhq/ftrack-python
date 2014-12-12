# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import sys
import traceback


class Error(Exception):
    '''ftrack specific error.'''

    default_message = 'Unspecified error occurred.'

    def __init__(self, message=None, details=None, **kw):
        '''Initialise exception with *message*.

        If *message* is None, the class 'default_message' will be used.

        '''
        if message is None:
            message = self.default_message

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

    default_message = 'Authentication error.'


class ServerError(Error):
    '''Raise when the server reports an error.'''

    default_message = 'Server reported error processing request.'


class NotFoundError(Error):
    '''Raise when something that should exist is not found.'''

    default_message = 'Not found.'


class NotUniqueError(Error):
    '''Raise when unique value required and duplicate detected.'''

    default_message = 'Non-unique value detected.'


class EntityTypeError(Error):
    '''Raise when an entity type error occurs.'''

    default_message = 'Entity type error.'


class UnrecognisedEntityTypeError(EntityTypeError):
    '''Raise when an unrecognised entity type detected.'''

    default_message = 'Entity type "{entity_type}" not recognised.'

    def __init__(self, entity_type, **kw):
        '''Initialise with *entity_type* that is unrecognised.'''
        self.entity_type = entity_type
        super(UnrecognisedEntityTypeError, self).__init__(**kw)


class InvalidStateError(Error):
    '''Raise when an invalid state detected.'''

    default_message = 'Invalid state.'


class InvalidStateTransitionError(InvalidStateError):
    '''Raise when an invalid state transition detected.'''

    default_message = (
        'Invalid transition from {current_state!r} to {target_state!r} state '
        'for entity {entity!r}'
    )

    def __init__(self, current_state, target_state, entity, **kw):
        '''Initialise error.'''
        self.current_state = current_state
        self.target_state = target_state
        self.entity = entity
        super(InvalidStateTransitionError, self).__init__(**kw)


class AttributeError(Error):
    '''Raise when an error related to an attribute occurs.'''

    default_message = 'Attribute error.'


class ImmutableAttributeError(AttributeError):
    '''Raise when modification of immutable attribute attempted.'''

    default_message = (
        'Cannot modify value of immutable {attribute.name!r} attribute.'
    )

    def __init__(self, attribute, **kw):
        '''Initialise error.'''
        self.attribute = attribute
        super(ImmutableAttributeError, self).__init__(**kw)


class CollectionError(Error):
    '''Raise when an error related to collections occurs.'''

    default_message = 'Collection error.'

    def __init__(self, collection, **kw):
        '''Initialise error.'''
        self.collection = collection
        super(CollectionError, self).__init__(**kw)


class ImmutableCollectionError(CollectionError):
    '''Raise when modification of immutable collection attempted.'''

    default_message = (
        'Cannot modify value of immutable collection {collection!r}.'
    )


class DuplicateItemInCollectionError(CollectionError):
    '''Raise when duplicate item in collection detected.'''

    default_message = (
        'Item {item!r} already exists in collection {collection!r}.'
    )

    def __init__(self, item, collection, **kw):
        '''Initialise error.'''
        self.item = item
        super(DuplicateItemInCollectionError, self).__init__(collection, **kw)


class ParseError(Error):
    '''Raise when a parsing error occurs.'''

    default_message = 'Failed to parse.'


class EventHubError(Error):
    '''Raise when issues related to event hub occur.'''

    default_message = 'Event hub error occurred.'


class EventHubConnectionError(EventHubError):
    '''Raise when event hub encounters connection problem.'''

    default_message = 'Event hub is not connected.'


class EventHubPacketError(EventHubError):
    '''Raise when event hub encounters an issue with a packet.'''

    default_message = 'Invalid packet.'
