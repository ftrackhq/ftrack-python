# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import pytest

import ftrack_api.inspection


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
    project_schema = session.query('ProjectSchema')[0]
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


def test_operation_optimisation_on_commit(session, mocker):
    '''Optimise operations on commit.'''
    mocked = mocker.patch.object(session, '_call')

    user_a = session.create('User', {'username': 'bob'})
    user_a['username'] = 'bob'
    user_a['email'] = 'bob@example.com'

    user_b = session.create('User', {'username': 'martin'})
    user_b['email'] = 'martin@ftrack.com'

    user_a['email'] = 'bob@example.com'

    user_c = session.create('User', {'username': 'neverexist'})
    user_c['email'] = 'ignore@example.com'
    session.delete(user_c)

    session.commit()

    # The above operations should have translated into three payloads to call
    # (two creates and one update).
    payloads = mocked.call_args[0][0]
    assert len(payloads) == 3

    user_a_entity_key = ftrack_api.inspection.primary_key(user_a).values()
    user_b_entity_key= ftrack_api.inspection.primary_key(user_b).values()

    assert payloads[0]['action'] == 'create'
    assert payloads[0]['entity_key'] == user_a_entity_key

    assert payloads[1]['action'] == 'create'
    assert payloads[1]['entity_key'] == user_b_entity_key

    assert payloads[2]['action'] == 'update'
    assert payloads[2]['entity_key'] == user_a_entity_key
