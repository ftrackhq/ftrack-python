# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import uuid

import pytest

import ftrack


@pytest.fixture(scope='session')
def session():
    '''Return session instance.'''
    return ftrack.Session()


@pytest.fixture()
def unique_name():
    '''Return a unique name.'''
    return 'test-{0}'.format(uuid.uuid4())


@pytest.fixture()
def unique_entity(request, session, unique_name):
    '''Return a newly created unique entity.'''
    entity = session.create('User', {'username': unique_name})
    session.commit()

    def cleanup():
        '''Remove created entity.'''
        session.delete(entity)
        session.commit()

    request.addfinalizer(cleanup)

    return entity


@pytest.fixture(scope='session')
def entity(session):
    '''Return the same entity for entire session.'''
    # Jenkins user
    entity = session.get('User', 'd07ae5d0-66e1-11e1-b5e9-f23c91df25eb')
    assert entity is not None

    return entity


@pytest.fixture()
def new_task(request, session, unique_name):
    '''Return a new task.'''
    project = session.query('Project')[0]
    project_schema = project['project_schema']
    default_task_type = project_schema.get_types('Task')[0]
    default_task_status = project_schema.get_statuses(
        'Task', default_task_type['id']
    )[0]

    task = session.create('Task', {
        'name': unique_name,
        'parent': project,
        'status': default_task_status,
        'type': default_task_type
    })

    session.commit()

    def cleanup():
        '''Remove created entity.'''
        session.delete(task)
        session.commit()

    request.addfinalizer(cleanup)

    return task


@pytest.fixture()
def new_scope(request, session, unique_name):
    '''Return a new scope.'''
    scope = session.create('Scope', {
        'name': unique_name
    })

    session.commit()

    def cleanup():
        '''Remove created entity.'''
        session.delete(scope)
        session.commit()

    request.addfinalizer(cleanup)

    return scope
