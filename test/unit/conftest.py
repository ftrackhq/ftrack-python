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
def new_user(request, session, unique_name):
    '''Return a newly created unique user.'''
    entity = session.create('User', {'username': unique_name})
    session.commit()

    def cleanup():
        '''Remove created entity.'''
        session.delete(entity)
        session.commit()

    request.addfinalizer(cleanup)

    return entity


@pytest.fixture(scope='session')
def user(session):
    '''Return the same user entity for entire session.'''
    # Jenkins user
    entity = session.get('User', 'd07ae5d0-66e1-11e1-b5e9-f23c91df25eb')
    assert entity is not None

    return entity


@pytest.fixture()
def new_task(request, session, unique_name):
    '''Return a new task.'''
    project = session.query(
        'Project where id is 5671dcb0-66de-11e1-8e6e-f23c91df25eb'
    )[0]
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


@pytest.fixture()
def new_review_session(request, session, unique_name):
    '''Return a new review session.'''

    # Create new review session on 'client review' test project.
    project = session.query(
        'Project where id is 81b98c47-5910-11e4-901f-3c0754282242'
    )[0]

    review_session = session.create('ReviewSession', {
        'name': unique_name,
        'description': unique_name,
        'project': project
    })

    session.commit()

    def cleanup():
        '''Remove created entity.'''
        session.delete(review_session)
        session.commit()

    request.addfinalizer(cleanup)

    return review_session


@pytest.fixture()
def new_review_session_object(request, session, unique_name):
    '''Return a new review session.'''

    # Create new review session on 'client review' test project.
    project = session.query(
        'Project where id is 81b98c47-5910-11e4-901f-3c0754282242'
    )[0]

    review_session = session.create('ReviewSession', {
        'name': unique_name,
        'description': unique_name,
        'project': project
    })

    # Get a reviewable AssetVersion from the 'client review' project.
    asset_version = session.get(
        'AssetVersion', 'a7519019-5910-11e4-804a-3c0754282242'
    )
    review_session_object = session.create('ReviewSessionObject', {
        'name': unique_name,
        'description': unique_name,
        'version': 'Version {0}'.format(asset_version['version']),
        'asset_version': asset_version,
        'review_session': review_session
    })

    session.commit()

    def cleanup():
        '''Remove created entity.'''
        session.delete(review_session)
        session.commit()

    request.addfinalizer(cleanup)

    return review_session_object
