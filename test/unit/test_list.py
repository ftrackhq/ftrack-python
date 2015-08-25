# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import uuid

import pytest
import ftrack_api.exception


@pytest.fixture()
def five_new_versions(request, session, new_task, user):
    '''Return 5 new versions.'''
    versions = []
    for i in range(5):
        asset = session.create('Asset', {
            'name': uuid.uuid4().hex,
            'context_id': new_task['parent_id'],
            'type_id': '44eb3ca8-4164-11df-9218-0019bb4983d8'
        })
        version = session.create('AssetVersion', {
            'asset_id': asset['id'],
            'user_id': user['id'],
            'status_id': '44de097a-4164-11df-9218-0019bb4983d8'
        })
        versions.append(version)

    session.commit()

    return versions


@pytest.fixture()
def five_new_tasks(request, session, new_project):
    '''Return 5 new tasks.'''
    project_schema = new_project['project_schema']
    default_task_type = project_schema.get_types('Task')[0]
    default_task_status = project_schema.get_statuses(
        'Task', default_task_type['id']
    )[0]

    tasks = []
    for i in range(5):
        task = session.create('Task', {
            'name': uuid.uuid4().hex,
            'parent': new_project,
            'status': default_task_status,
            'type': default_task_type
        })
        tasks.append(task)

    session.commit()

    return tasks


@pytest.fixture()
def list_category(session):
    '''Return a list category.'''
    entity = session.get('ListCategory', '87d974d2-d6f7-11e1-8930-f23c91df25eb')
    assert entity is not None

    return entity


@pytest.mark.parametrize('list_type', [
    'task',
    'asset_version'
], ids=[
    'task',
    'asset_version'
])
def test_create_list(list_type, session, project, unique_name,
                     list_category, user):
    '''Create a new list of *list_type*.'''
    session.create('List', {
        'name': unique_name,
        'project': project,
        'type': list_type,
        'category': list_category,
        'user': user
    })

    session.commit()

    new_list = session.query('List where name is {0}'.format(unique_name)).one()

    assert new_list['type'] == list_type, 'List type is correct'


def test_create_list_with_bad_type(session, project, unique_name, list_category,
                                   user):
    '''Create a list with bad type.'''
    with pytest.raises(ftrack_api.exception.ServerError):
        session.create('List', {
            'name': unique_name,
            'project': project,
            'type': 'bad_type',
            'category': list_category,
            'user': user
        })

        session.commit()

    session.reset()


def test_create_asset_version_list_with_versions(
    session, project, unique_name, list_category, user, five_new_versions
):
    '''Create a list with asset versions.'''
    asset_version_list = session.create('AssetVersionList', {
        'name': unique_name,
        'project': project,
        'category': list_category,
        'user': user
    })

    for version in five_new_versions:
        asset_version_list['items'].append(version)

    session.commit()
    session.reset()

    asset_version_list = session.query(
        'List where name is {0}'.format(unique_name)
    ).one()

    assert len(asset_version_list['items']) == 5, 'Contains 5 versions.'


def test_create_list_with_tasks(
    session, unique_name, list_category, user, five_new_tasks
):
    '''Create a list with tasks.'''
    task_list = session.create('AbstractTaskList', {
        'name': unique_name,
        'project': five_new_tasks[0]['project'],
        'category': list_category,
        'user': user
    })

    for task in five_new_tasks:
        task_list['items'].append(task)

    session.commit()
    session.reset()

    task_list = session.query(
        'List where name is {0}'.format(unique_name)
    ).one()

    assert len(task_list['items']) == 5, 'Contains 5 tasks.'


def test_add_task_to_version_list(
    session, new_task, user, list_category, unique_name
):
    '''Add a task to a version list.'''
    asset_version_list = session.create('AssetVersionList', {
        'name': unique_name,
        'project': new_task['project'],
        'category': list_category,
        'user': user
    })

    asset_version_list['items'].append(new_task)

    with pytest.raises(ftrack_api.exception.ServerError):
        session.commit()

    session.reset()


def test_remove_task_from_list(
    session, unique_name, list_category, user, five_new_tasks
):
    '''Remove a task from a list.'''
    task_list = session.create('AbstractTaskList', {
        'name': unique_name,
        'project': five_new_tasks[0]['project'],
        'category': list_category,
        'user': user
    })

    for task in five_new_tasks:
        task_list['items'].append(task)

    session.commit()
    session.reset()

    task_list = session.query(
        'List where name is {0}'.format(unique_name)
    ).one()

    task_list['items'].remove(five_new_tasks[2])

    session.commit()
    session.reset()

    task_list = session.query(
        'List where name is {0}'.format(unique_name)
    ).one()

    assert len(task_list['items']) == 4, 'Contains 4 tasks.'
