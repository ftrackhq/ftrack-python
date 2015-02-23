# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import pytest


def test_get_entity_bypassing_cache(session, unique_entity):
    '''Retrieve an entity by type and id bypassing cache.'''
    session.cache.remove(
        session.cache_key_maker.key(unique_entity.identity)
    )
    matching = session.get(*unique_entity.identity)

    # Check a different instance returned.
    assert matching is not unique_entity

    # Check instances have the same identity.
    assert matching == unique_entity


def test_get_entity_from_cache(session, unique_entity):
    '''Retrieve an entity by type and id from cache.'''
    matching = session.get(*unique_entity.identity)
    assert matching is unique_entity


def test_get_non_existant_entity(session):
    '''Retrieve a non-existant entity by type and id.'''
    matching = session.get('User', 'non-existant-id')
    assert matching is None


def test_get_entity_of_invalid_type(session):
    '''Fail to retrieve an entity using an invalid type.'''
    with pytest.raises(KeyError):
        session.get('InvalidType', 'id')
