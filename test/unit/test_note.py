# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack


def test_create_reply(session, new_note, user, unique_name):
    '''Test create reply on *new_note*.'''
    reply_text = 'My reply on note'
    new_note.create_reply(reply_text, user)

    session.commit()

    assert len(new_note['notes']) == 1

    assert reply_text == new_note['notes'][0]['text']
