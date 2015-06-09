# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import uuid

import pytest

import ftrack_api


@pytest.fixture(scope='session')
def session():
    '''Return session instance.'''
    return ftrack_api.Session()


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


@pytest.fixture()
def user(session):
    '''Return the same user entity for entire session.'''
    # Jenkins user
    entity = session.get('User', 'd07ae5d0-66e1-11e1-b5e9-f23c91df25eb')
    assert entity is not None

    return entity


@pytest.fixture()
def new_project(request, session, user):
    '''Return new project with basic tree.'''
    project_schema = session.query('ProjectSchema')[0]
    default_shot_status = project_schema.get_statuses('Shot')[0]
    default_task_type = project_schema.get_types('Task')[0]
    default_task_status = project_schema.get_statuses(
        'Task', default_task_type['id']
    )[0]

    project_name = 'python_api_test_{0}'.format(uuid.uuid1().hex)
    project = session.create('Project', {
        'name': project_name,
        'full_name': project_name + '_full',
        'project_schema': project_schema
    })

    for sequence_number in range(1):
        sequence = session.create('Sequence', {
            'name': 'sequence_{0:03d}'.format(sequence_number),
            'parent': project
        })

        for shot_number in range(1):
            shot = session.create('Shot', {
                'name': 'shot_{0:03d}'.format(shot_number * 10),
                'parent': sequence,
                'status': default_shot_status
            })

            for task_number in range(1):
                task = session.create('Task', {
                    'name': 'task_{0:03d}'.format(task_number),
                    'parent': shot,
                    'status': default_task_status,
                    'type': default_task_type
                })

                session.create('Appointment', {
                    'type': 'assignment',
                    'context': task,
                    'resource': user
                })

    session.commit()

    def cleanup():
        '''Remove created entity.'''
        session.delete(project)
        session.commit()

    request.addfinalizer(cleanup)

    return project


@pytest.fixture(scope='session')
def project(session):
    '''Return same project for entire session.'''
    # Test project.
    entity = session.get('Project', '5671dcb0-66de-11e1-8e6e-f23c91df25eb')
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


@pytest.fixture(scope='session')
def task(session):
    '''Return same task for entire session.'''
    # Tests/python_api/tasks/t1
    entity = session.get('Task', 'adb4ad6c-7679-11e2-8df2-f23c91df25eb')
    assert entity is not None

    return entity


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
def new_note(request, session, unique_name, new_task, user):
    '''Return a new note.'''

    note = new_task.create_note(unique_name, user)

    session.commit()

    def cleanup():
        '''Remove created entity.'''
        session.delete(note)
        session.commit()

    request.addfinalizer(cleanup)

    return note
