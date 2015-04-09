# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import uuid


class Event(dict):
    '''Represent a single event.'''

    def __init__(self, topic, id=None, data=None, sent=None,
                 source=None, target='', in_reply_to_event=None):
        '''Initialise event.

        *topic* is the required topic for the event. It can use a dotted
        notation to demarcate groupings. For example, 'ftrack.update'.

        *id* is the unique id for this event instance. It is primarily used when
        replying to an event. If not supplied a default uuid based value will
        be used.

        *data* refers to event specific data. It should be a mapping structure
        and defaults to an empty dictionary if not supplied.

        *sent* is the timestamp the event is sent. It will be set automatically
        as send time unless specified here.

        *source* is information about where the event originated. It should be
        a mapping and include at least a unique id value under an 'id' key. If
        not specified, senders usually populate the value automatically at
        publish time.

        *target* can be an expression that targets this event. For example,
        a reply event would target the event to the sender of the source event.
        The expression will be tested against subscriber information only.

        *in_reply_to_event* is used when replying to an event and should contain
        the unique id of the event being replied to.

        '''
        super(Event, self).__init__(
            id=id or uuid.uuid4().hex,
            data=data or {},
            topic=topic,
            sent=sent,
            source=source or {},
            target=target,
            in_reply_to_event=in_reply_to_event
        )

        self._stopped = False

    def stop(self):
        '''Stop further processing of this event.'''
        self._stopped = True

    def is_stopped(self):
        '''Return whether event has been stopped.'''
        return self._stopped

    def __str__(self):
        '''Return string representation.'''
        return '<{0} {1}>'.format(
            self.__class__.__name__, super(Event, self).__str__()
        )
