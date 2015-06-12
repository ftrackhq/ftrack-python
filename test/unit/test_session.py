# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import pytest

import ftrack_api.inspection
import ftrack_api.symbol


def test_get_entity(session, user):
    '''Retrieve an entity by type and id.'''
    matching = session.get(*ftrack_api.inspection.identity(user))
    assert matching == user


def test_get_non_existant_entity(session):
    '''Retrieve a non-existant entity by type and id.'''
    matching = session.get('User', 'non-existant-id')
    assert matching is None


def test_get_entity_of_invalid_type(session):
    '''Fail to retrieve an entity using an invalid type.'''
    with pytest.raises(KeyError):
        session.get('InvalidType', 'id')


def test_get_entity_with_composite_primary_key(session, new_project):
    '''Retrieve entity that uses a composite primary key.'''
    entity = session.create('Metadata', {
        'key': 'key', 'value': 'value',
        'parent_type': new_project.entity_type,
        'parent_id':  new_project['id']
    })

    session.commit()

    # Avoid cache.
    new_session = ftrack_api.Session()
    retrieved_entity = new_session.get(
        'Metadata', ftrack_api.inspection.primary_key(entity).values()
    )

    assert retrieved_entity == entity


def test_get_entity_with_incomplete_composite_primary_key(session, new_project):
    '''Fail to retrieve entity using incomplete composite primary key.'''
    entity = session.create('Metadata', {
        'key': 'key', 'value': 'value',
        'parent_type': new_project.entity_type,
        'parent_id':  new_project['id']
    })

    session.commit()

    # Avoid cache.
    new_session = ftrack_api.Session()
    with pytest.raises(ValueError):
        new_session.get(
            'Metadata', ftrack_api.inspection.primary_key(entity).values()[0]
        )


def test_populate_entity(session, new_user):
    '''Populate entity that uses single primary key.'''
    with session.auto_populating(False):
        assert new_user['email'] is ftrack_api.symbol.NOT_SET

    session.populate(new_user, 'email')
    assert new_user['email'] is not ftrack_api.symbol.NOT_SET


def test_populate_entities(session, unique_name):
    '''Populate multiple entities that use single primary key.'''
    users = []
    for index in range(3):
        users.append(
            session.create(
                'User', {'username': '{0}-{1}'.format(unique_name, index)}
            )
        )

    session.commit()

    with session.auto_populating(False):
        for user in users:
            assert user['email'] is ftrack_api.symbol.NOT_SET

    session.populate(users, 'email')

    for user in users:
        assert user['email'] is not ftrack_api.symbol.NOT_SET


def test_populate_entity_with_composite_primary_key(session, new_project):
    '''Populate entity that uses a composite primary key.'''
    entity = session.create('Metadata', {
        'key': 'key', 'value': 'value',
        'parent_type': new_project.entity_type,
        'parent_id':  new_project['id']
    })

    session.commit()

    # Avoid cache.
    new_session = ftrack_api.Session()
    retrieved_entity = new_session.get(
        'Metadata', ftrack_api.inspection.primary_key(entity).values()
    )

    # Manually change already populated remote value so can test it gets reset
    # on populate call.
    retrieved_entity.attributes.get('value').set_remote_value(
        retrieved_entity, 'changed'
    )

    new_session.populate(retrieved_entity, 'value')
    assert retrieved_entity['value'] == 'value'
