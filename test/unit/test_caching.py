# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import ftrack_api.inspection


def test_get_entity_bypassing_cache(session, user, mocker):
    '''Retrieve an entity by type and id bypassing cache.'''
    mocker.patch.object(session, '_call', wraps=session._call)

    session.cache.remove(
        session.cache_key_maker.key(ftrack_api.inspection.identity(user))
    )
    matching = session.get(*ftrack_api.inspection.identity(user))

    # Check a different instance returned.
    assert matching is not user

    # Check instances have the same identity.
    assert matching == user

    # Check cache was bypassed and server was called.
    assert session._call.called


def test_get_entity_from_cache(session, user, mocker):
    '''Retrieve an entity by type and id from cache.'''
    mocker.patch.object(session, '_call')

    matching = session.get(*ftrack_api.inspection.identity(user))
    assert matching is user

    # Check that no call was made to server.
    assert not session._call.called
