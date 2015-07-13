# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import copy
import uuid

import mock
import pytest

import ftrack_api.collection
import ftrack_api.symbol
import ftrack_api.inspection


@pytest.fixture
def mock_entity(session):
    '''Return mock entity.'''
    entity = mock.MagicMock()
    entity.session = session
    entity.primary_key_attributes = ['id']
    entity['id'] = str(uuid.uuid4())
    return entity


@pytest.fixture
def mock_attribute():
    '''Return mock attribute.'''
    attribute = mock.MagicMock()
    attribute.name = 'test'
    return attribute


def test_initialisation_does_not_modify_entity_state(
    mock_entity, mock_attribute
):
    '''Initialising collection does not modify entity state.'''
    ftrack_api.collection.Collection(
        mock_entity, mock_attribute, data=[1, 2]
    )

    assert ftrack_api.inspection.state(mock_entity) is ftrack_api.symbol.NOT_SET


def test_collection_shallow_copy(mock_entity, mock_attribute):
    '''Shallow copying collection should avoid indirect mutation.'''
    collection = ftrack_api.collection.Collection(
        mock_entity, mock_attribute, data=[1, 2]
    )

    with mock_entity.session.operation_recording(False):
        collection_copy = copy.copy(collection)
        collection_copy.append(3)

    assert list(collection) == [1, 2]
    assert list(collection_copy) == [1, 2, 3]


def test_immutable_collection_initialisation(mock_entity, mock_attribute):
    '''Initialise immutable collection.'''
    collection = ftrack_api.collection.Collection(
        mock_entity, mock_attribute, data=[1, 2], mutable=False
    )

    assert list(collection) == [1, 2]
    assert collection.mutable is False


def test_mapped_collection_proxy_shallow_copy(new_project, unique_name):
    '''Shallow copying mapped collection proxy avoids indirect mutation.'''
    metadata = new_project['metadata']

    with new_project.session.operation_recording(False):
        metadata_copy = copy.copy(metadata)
        metadata_copy[unique_name] = True

    assert unique_name not in metadata
    assert unique_name in metadata_copy
