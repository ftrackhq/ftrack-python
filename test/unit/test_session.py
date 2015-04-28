# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import pytest

import ftrack.inspection


def test_get_entity(session, user):
    '''Retrieve an entity by type and id.'''
    matching = session.get(*ftrack.inspection.identity(user))
    assert matching == user


def test_get_non_existant_entity(session):
    '''Retrieve a non-existant entity by type and id.'''
    matching = session.get('User', 'non-existant-id')
    assert matching is None


def test_get_entity_of_invalid_type(session):
    '''Fail to retrieve an entity using an invalid type.'''
    with pytest.raises(KeyError):
        session.get('InvalidType', 'id')
