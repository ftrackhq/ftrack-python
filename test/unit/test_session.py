# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import pytest

import ftrack.inspection


def test_get_entity_bypassing_cache(session, user):
    '''Retrieve an entity by type and id bypassing cache.'''
    session.cache.remove(
        session.cache_key_maker.key(ftrack.inspection.identity(user))
    )
    matching = session.get(*ftrack.inspection.identity(user))

    # Check a different instance returned.
    assert matching is not user

    # Check instances have the same identity.
    assert matching == user


def test_get_entity_from_cache(session, user, mocker):
    '''Retrieve an entity by type and id from cache.'''
    mocker.patch.object(session, '_call')

    matching = session.get(*ftrack.inspection.identity(user))
    assert matching is user

    # Check that no call was made to server.
    assert not session._call.called


def test_get_non_existant_entity(session):
    '''Retrieve a non-existant entity by type and id.'''
    matching = session.get('User', 'non-existant-id')
    assert matching is None


def test_get_entity_of_invalid_type(session):
    '''Fail to retrieve an entity using an invalid type.'''
    with pytest.raises(KeyError):
        session.get('InvalidType', 'id')
