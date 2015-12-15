# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import inspect

import pytest

import ftrack_api.structure.standard


@pytest.fixture(scope='session')
def structure():
    '''Return structure.'''
    return ftrack_api.structure.standard.StandardStructure()


@pytest.fixture()
def asset_version_with_project_tree(new_project_tree):
    session = new_project_tree.session
    shot = session.query(
        'Shot where project_id is "{}"'.format(new_project_tree['id'])
    ).first()
    asset = session.create('Asset', {
        'name': 'my_new_asset',
        'parent': shot
    })
    asset_version = session.create('AssetVersion', {
        'asset': asset
    })
    return asset_version


def test_file_component(asset_version_with_project_tree, structure):
    session = asset_version_with_project_tree.session
    component = session.create('FileComponent', {
        'name': 'main',
        'file_type': '.exr',
        'version': asset_version_with_project_tree
    })
    session.commit()

    project = asset_version_with_project_tree['asset']['parent']['project']

    assert structure.get_resource_identifier(component) == (
        '{}/sequence_000/shot_000/my_new_asset/v001/main.exr'.format(
            project['name']
        )
    )


def test_sequence_component(
    asset_version_with_project_tree, structure, temporary_sequence
):
    session = asset_version_with_project_tree.session
    component = session.create_component(
        temporary_sequence, location=None,
        data={
            'version': asset_version_with_project_tree,
            'name': 'foobar'
        }
    )
    session.commit()

    project = asset_version_with_project_tree['asset']['parent']['project']

    assert structure.get_resource_identifier(component) == (
        '{}/sequence_000/shot_000/my_new_asset/v001/foobar.%04d.jpg'.format(
            project['name']
        )
    )

    assert structure.get_resource_identifier(component['members'][2]) == (
        '{}/sequence_000/shot_000/my_new_asset/v001/foobar.0002.jpg'.format(
            project['name']
        )
    )


def test_container_component(asset_version_with_project_tree, structure):
    session = asset_version_with_project_tree.session
    container = session.create('ContainerComponent', {
        'name': 'foo',
        'version': asset_version_with_project_tree
    })
    component = session.create('FileComponent', {
        'file_type': '.mov',
        'name': 'bar',
        'container': container
    })
    session.commit()

    project = asset_version_with_project_tree['asset']['parent']['project']

    assert structure.get_resource_identifier(container) == (
        '{}/sequence_000/shot_000/my_new_asset/v001/foo'.format(
            project['name']
        )
    )

    assert structure.get_resource_identifier(component) == (
        '{}/sequence_000/shot_000/my_new_asset/v001/foo/bar.mov'.format(
            project['name']
        )
    )


def unsupported_entity():
    '''Return an unsupported entity.'''


@pytest.mark.parametrize('entity, context, expected', [

])
def test_get_resource_identifier(structure, entity, context, expected):
    '''Get resource identifier.'''
