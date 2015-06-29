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


def test_delete_operation_ordering(session, unique_name):
    '''Delete entities in valid order.'''
    # Construct entities.
    project_schema = session.query('ProjectSchema').first()
    project = session.create('Project', {
        'name': unique_name,
        'full_name': unique_name,
        'project_schema': project_schema
    })

    sequence = session.create('Sequence', {
        'name': unique_name,
        'parent': project
    })

    session.commit()

    # Delete in order that should succeed.
    session.delete(sequence)
    session.delete(project)

    session.commit()


def test_create_then_delete_operation_ordering(session, unique_name):
    '''Create and delete entity in one transaction.'''
    entity = session.create('User', {'username': unique_name})
    session.delete(entity)
    session.commit()


def test_create_and_modify_to_have_required_attribute(session, unique_name):
    '''Create and modify entity to have required attribute in transaction.'''
    entity = session.create('Scope', {})
    other = session.create('Scope', {'name': unique_name})
    entity['name'] = '{0}2'.format(unique_name)
    session.commit()


def test_ignore_in_create_entity_payload_values_set_to_not_set(
    mocker, unique_name, session
):
    '''Ignore in commit, created entity data set to NOT_SET'''
    mocked = mocker.patch.object(session, '_call')

    # Should ignore 'email' attribute in payload.
    new_user = session.create(
        'User', {'username': unique_name, 'email': 'test'}
    )
    new_user['email'] = ftrack_api.symbol.NOT_SET
    session.commit()
    payloads = mocked.call_args[0][0]
    assert len(payloads) == 1


def test_ignore_operation_that_modifies_attribute_to_not_set(
    mocker, session, user
):
    '''Ignore in commit, operation that sets attribute value to NOT_SET'''
    mocked = mocker.patch.object(session, '_call')

    # Should result in no call to server.
    user['email'] = ftrack_api.symbol.NOT_SET
    session.commit()

    assert not mocked.called


def test_operation_optimisation_on_commit(session, mocker):
    '''Optimise operations on commit.'''
    mocked = mocker.patch.object(session, '_call')

    user_a = session.create('User', {'username': 'bob'})
    user_a['username'] = 'foo'
    user_a['email'] = 'bob@example.com'

    user_b = session.create('User', {'username': 'martin'})
    user_b['email'] = 'martin@ftrack.com'

    user_a['email'] = 'bob@example.com'
    user_a['first_name'] = 'Bob'

    user_c = session.create('User', {'username': 'neverexist'})
    user_c['email'] = 'ignore@example.com'
    session.delete(user_c)

    user_a_entity_key = ftrack_api.inspection.primary_key(user_a).values()
    user_b_entity_key = ftrack_api.inspection.primary_key(user_b).values()

    session.commit()

    # The above operations should have translated into three payloads to call
    # (two creates and one update).
    payloads = mocked.call_args[0][0]
    assert len(payloads) == 3

    assert payloads[0]['action'] == 'create'
    assert payloads[0]['entity_key'] == user_a_entity_key
    assert set(payloads[0]['entity_data'].keys()) == set([
        '__entity_type__', 'id', 'resource_type', 'username'
    ])

    assert payloads[1]['action'] == 'create'
    assert payloads[1]['entity_key'] == user_b_entity_key
    assert set(payloads[1]['entity_data'].keys()) == set([
        '__entity_type__', 'id', 'resource_type', 'username', 'email'
    ])

    assert payloads[2]['action'] == 'update'
    assert payloads[2]['entity_key'] == user_a_entity_key
    assert set(payloads[2]['entity_data'].keys()) == set([
        '__entity_type__', 'email', 'first_name'
    ])


def test_state_collection(session, unique_name, user):
    '''Session state collection holds correct entities.'''
    # NOT_SET
    user_a = session.create('User', {'username': unique_name})
    session.commit()

    # CREATED
    user_b = session.create('User', {'username': unique_name})
    user_b['username'] = 'changed'

    # MODIFIED
    user_c = user
    user_c['username'] = 'changed'

    # DELETED
    user_d = session.create('User', {'username': unique_name})
    session.delete(user_d)

    assert session.created == [user_b]
    assert session.modified == [user_c]
    assert session.deleted == [user_d]


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
