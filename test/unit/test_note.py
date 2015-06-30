# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import ftrack_api


def test_create_reply(session, new_note, user, unique_name):
    '''Test create reply on *new_note*.'''
    reply_text = 'My reply on note'
    new_note.create_reply(reply_text, user)

    session.commit()

    assert len(new_note['replies']) == 1

    assert reply_text == new_note['replies'][0]['text']


def test_create_note_on_asset_version(session, user, unique_name):
    '''Test create note method on asset version.'''
    asset_version = session.query('AssetVersion').all()[0]

    notes_count = len(asset_version['notes'])

    note = asset_version.create_note(unique_name, user)

    session.commit()

    new_session = ftrack_api.Session()

    assert (
        len(new_session.get('AssetVersion', asset_version['id'])['notes'])
        == (notes_count + 1)
    )

    session.delete(note)
    session.commit()
