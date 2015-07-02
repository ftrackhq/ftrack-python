# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import copy
import uuid

import ftrack_api.collection
import ftrack_api.symbol
import ftrack_api.inspection


def test_initialisation_does_not_modify_entity_state(new_user):
    '''Initialising collection does not modify entity state.'''
    ftrack_api.collection.Collection(
        new_user, None, data=[1, 2]
    )

    assert ftrack_api.inspection.state(new_user) is ftrack_api.symbol.NOT_SET


def test_collection_shallow_copy(new_user):
    '''Shallow copying collection should avoid indirect mutation.'''
    collection = ftrack_api.collection.Collection(
        new_user, None, data=[1, 2]
    )

    with new_user.session.operation_recording(False):
        collection_copy = copy.copy(collection)
        collection_copy.append(3)

    assert set(collection) == set([1, 2])
    assert set(collection_copy) == set([1, 2, 3])


def test_mapped_collection_proxy_shallow_copy(new_project, unique_name):
    '''Shallow copying mapped collection proxy avoids indirect mutation.'''
    metadata = new_project['metadata']

    with new_project.session.operation_recording(False):
        metadata_copy = copy.copy(metadata)
        metadata_copy[unique_name] = True

    assert unique_name not in metadata
    assert unique_name in metadata_copy
