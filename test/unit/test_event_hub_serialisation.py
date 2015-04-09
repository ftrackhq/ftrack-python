# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack
import json


def test_encode(session):
    '''Encode event data.'''
    encoded = session.event_hub._encode({
        'in_reply_to_event': 'id'
    })

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
