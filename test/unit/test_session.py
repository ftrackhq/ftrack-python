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


def test_operation_ordering(session, unique_name):
    '''Perform operations in predictable order on commit.'''
    # Delete ordering.
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

    session.delete(sequence)
    session.delete(project)

    # Should not fail.
    session.commit()

