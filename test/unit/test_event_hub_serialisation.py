# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import json

import ftrack_api.event.base


def test_encode(session):
    '''Encode event data.'''
    encoded = session.event_hub._encode(
        dict(name='ftrack.event', args=[ftrack_api.event.base.Event('test')])
    )
    assert 'inReplyToEvent' in encoded
    assert 'in_reply_to_event' not in encoded


def test_decode(session):
    '''Decode event data.'''
    decoded = session.event_hub._decode(
        json.dumps({
            'inReplyToEvent': 'id'
        })
    )

    assert 'in_reply_to_event' in decoded
    assert 'inReplyToEvent' not in decoded
