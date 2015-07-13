# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import copy
import uuid

import mock
import pytest

import ftrack_api.collection
import ftrack_api.symbol
import ftrack_api.inspection
import ftrack_api.exception
import ftrack_api.operation


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


def test_collection_initialisation_does_not_modify_entity_state(
    mock_entity, mock_attribute
):
    '''Initialising collection does not modify entity state.'''
    ftrack_api.collection.Collection(
        mock_entity, mock_attribute, data=[1, 2]
    )

    assert ftrack_api.inspection.state(mock_entity) is ftrack_api.symbol.NOT_SET


def test_immutable_collection_initialisation(mock_entity, mock_attribute):
    '''Initialise immutable collection.'''
    collection = ftrack_api.collection.Collection(
        mock_entity, mock_attribute, data=[1, 2], mutable=False
    )

    assert list(collection) == [1, 2]
    assert collection.mutable is False


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


def test_collection_insert(mock_entity, mock_attribute):
    '''Insert a value into collection.'''
    collection = ftrack_api.collection.Collection(
        mock_entity, mock_attribute, data=[1, 2]
    )

    collection.insert(0, 0)
    assert list(collection) == [0, 1, 2]


def test_collection_insert_duplicate(mock_entity, mock_attribute):
    '''Fail to insert a duplicate value into collection.'''
    collection = ftrack_api.collection.Collection(
        mock_entity, mock_attribute, data=[1, 2]
    )

    with pytest.raises(ftrack_api.exception.DuplicateItemInCollectionError):
        collection.insert(0, 1)


def test_immutable_collection_insert(mock_entity, mock_attribute):
    '''Fail to insert a value into immutable collection.'''
    collection = ftrack_api.collection.Collection(
        mock_entity, mock_attribute, data=[1, 2], mutable=False
    )

    with pytest.raises(ftrack_api.exception.ImmutableCollectionError):
        collection.insert(0, 0)


def test_collection_set_item(mock_entity, mock_attribute):
    '''Set item at index in collection.'''
    collection = ftrack_api.collection.Collection(
        mock_entity, mock_attribute, data=[1, 2]
    )

    collection[0] = 0
    assert list(collection) == [0, 2]


def test_collection_re_set_item(mock_entity, mock_attribute):
    '''Re-set value at exact same index in collection.'''
    collection = ftrack_api.collection.Collection(
        mock_entity, mock_attribute, data=[1, 2]
    )

    collection[0] = 1
    assert list(collection) == [1, 2]


def test_collection_set_duplicate_item(mock_entity, mock_attribute):
    '''Fail to set a duplicate value into collection at different index.'''
    collection = ftrack_api.collection.Collection(
        mock_entity, mock_attribute, data=[1, 2]
    )

    with pytest.raises(ftrack_api.exception.DuplicateItemInCollectionError):
        collection[0] = 2


def test_immutable_collection_set_item(mock_entity, mock_attribute):
    '''Fail to set item at index in immutable collection.'''
    collection = ftrack_api.collection.Collection(
        mock_entity, mock_attribute, data=[1, 2], mutable=False
    )

    with pytest.raises(ftrack_api.exception.ImmutableCollectionError):
        collection[0] = 0


def test_collection_delete_item(mock_entity, mock_attribute):
    '''Remove item at index from collection.'''
    collection = ftrack_api.collection.Collection(
        mock_entity, mock_attribute, data=[1, 2]
    )
    del collection[0]
    assert list(collection) == [2]


def test_collection_delete_item_at_invalid_index(mock_entity, mock_attribute):
    '''Fail to remove item at missing index from immutable collection.'''
    collection = ftrack_api.collection.Collection(
        mock_entity, mock_attribute, data=[1, 2]
    )

    with pytest.raises(IndexError):
        del collection[4]


def test_immutable_collection_delete_item(mock_entity, mock_attribute):
    '''Fail to remove item at index from immutable collection.'''
    collection = ftrack_api.collection.Collection(
        mock_entity, mock_attribute, data=[1, 2], mutable=False
    )

    with pytest.raises(ftrack_api.exception.ImmutableCollectionError):
        del collection[0]


def test_collection_count(mock_entity, mock_attribute):
    '''Count items in collection.'''
    collection = ftrack_api.collection.Collection(
        mock_entity, mock_attribute, data=[1, 2]
    )
    assert len(collection) == 2

    collection.append(3)
    assert len(collection) == 3

    del collection[0]
    assert len(collection) == 2


@pytest.mark.parametrize('other, expected', [
    ([], False),
    ([1, 2], True),
    ([1, 2, 3], False),
    ([1], False)
], ids=[
    'empty',
    'same',
    'additional',
    'missing'
])
def test_collection_equal(mocker, mock_entity, mock_attribute, other, expected):
    '''Determine collection equality against another collection.'''
    collection_a = ftrack_api.collection.Collection(
        mock_entity, mock_attribute, data=[1, 2]
    )

    collection_b = ftrack_api.collection.Collection(
        mock_entity, mock_attribute, data=other
    )

    # Temporarily override determination of entity identity so that it works
    # against simple scalar values for purpose of test.
    mocker.patch.object(
        ftrack_api.inspection, 'identity', lambda entity: str(entity)
    )
    assert (collection_a == collection_b) is expected


def test_collection_not_equal_to_non_collection(mock_entity, mock_attribute):
    '''Collection not equal to a non-collection.'''
    collection = ftrack_api.collection.Collection(
        mock_entity, mock_attribute, data=[1, 2]
    )

    assert (collection != {}) is True


def test_collection_notify_on_modification(
    mock_entity, mock_attribute, session
):
    '''Record UpdateEntityOperation on collection modification.'''
    collection = ftrack_api.collection.Collection(
        mock_entity, mock_attribute, data=[1, 2]
    )
    assert len(session.recorded_operations) == 0

    collection.append(3)
    assert len(session.recorded_operations) == 1
    operation = session.recorded_operations.pop()
    assert isinstance(operation, ftrack_api.operation.UpdateEntityOperation)
    assert operation.new_value == list(collection)


def test_mapped_collection_proxy_shallow_copy(new_project, unique_name):
    '''Shallow copying mapped collection proxy avoids indirect mutation.'''
    metadata = new_project['metadata']

    with new_project.session.operation_recording(False):
        metadata_copy = copy.copy(metadata)
        metadata_copy[unique_name] = True

    assert unique_name not in metadata
    assert unique_name in metadata_copy
