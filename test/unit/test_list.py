# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import uuid

import pytest
import ftrack_api.exception


@pytest.fixture()
def new_versions(request, session, new_task, user):
    '''Return a new versions.'''
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
    session, project, unique_name, list_category, user, new_versions
):
    '''Create a list with asset versions.'''
    asset_version_list = session.create('AssetVersionList', {
        'name': unique_name,
        'project': project,
        'category': list_category,
        'user': user
    })

    for version in new_versions:
        asset_version_list['items'].append(version)

    session.commit()
    session.reset()

    asset_version_list = session.query(
        'List where name is {0}'.format(unique_name)
    ).one()

    assert len(asset_version_list['items']) == 5, 'Must contain 5 versions.'
