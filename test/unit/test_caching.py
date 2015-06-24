# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import tempfile
import functools
import uuid

import pytest

import ftrack_api
import ftrack_api.cache
import ftrack_api.inspection
import ftrack_api.symbol


@pytest.fixture(params=['memory', 'persisted'])
def cache(request):
    '''Return cache.'''
    if request.param == 'memory':
        cache = None  # There is already a default Memory cache present.
    elif request.param == 'persisted':
        cache_path = os.path.join(
            tempfile.gettempdir(), '{0}.dbm'.format(uuid.uuid4().hex)
        )

        cache = lambda session: ftrack_api.cache.SerialisedCache(
            ftrack_api.cache.FileCache(cache_path),
            encode=functools.partial(
                session.encode, entity_attribute_strategy='persisted_only'
            ),
            decode=session.decode
        )

        def cleanup():
            '''Cleanup.'''
            try:
                os.remove(cache_path)
            except OSError:
                # BSD DB (Mac OSX) implementation of the interface will append 
                # a .db extension.
                os.remove(cache_path + '.db')

        request.addfinalizer(cleanup)

    return cache


def test_get_entity_bypassing_cache(session, user, mocker):
    '''Retrieve an entity by type and id bypassing cache.'''
    mocker.patch.object(session, '_call', wraps=session._call)

    session.cache.remove(
        session.cache_key_maker.key(ftrack_api.inspection.identity(user))
    )
    session._detach(user)

    matching = session.get(*ftrack_api.inspection.identity(user))

    # Check a different instance returned.
    assert matching is not user

    # Check instances have the same identity.
    assert matching == user

    # Check cache was bypassed and server was called.
    assert session._call.called


def test_get_entity_from_cache(cache, task, mocker):
    '''Retrieve an entity by type and id from cache.'''
    session = ftrack_api.Session(cache=cache)

    # Prepare cache.
    session.merge(task)

    # Disable server calls.
    mocker.patch.object(session, '_call')

    # Retrieve entity from cache.
    entity = session.get(*ftrack_api.inspection.identity(task))

    assert entity is not None, 'Failed to retrieve entity from cache.'
    assert entity == task
    assert entity is not task

    # Check that no call was made to server.
    assert not session._call.called


def test_get_entity_tree_from_cache(cache, new_project_tree, mocker):
    '''Retrieve an entity tree from cache.'''
    session = ftrack_api.Session(cache=cache)

    # Prepare cache.
    # TODO: Maybe cache should be prepopulated for a better check here.
    session.query(
        'select children, children.children, children.children.children, '
        'children.children.children.assignments, '
        'children.children.children.assignments.resource '
        'from Project where id is "{0}"'
        .format(new_project_tree['id'])
    ).one()

    # Disable server calls.
    mocker.patch.object(session, '_call')

    # Retrieve entity from cache.
    entity = session.get(*ftrack_api.inspection.identity(new_project_tree))

    assert entity is not None, 'Failed to retrieve entity from cache.'
    assert entity == new_project_tree
    assert entity is not new_project_tree

    # Check tree.
    with session.auto_populating(False):
        for sequence in entity['children']:
            for shot in sequence['children']:
                for task in shot['children']:
                    assignments = task['assignments']
                    for assignment in assignments:
                        resource = assignment['resource']

                        assert resource is not ftrack_api.symbol.NOT_SET

    # Check that no call was made to server.
    assert not session._call.called


def test_get_metadata_from_cache(session, mocker, cache, new_task):
    '''Retrieve an entity along with its metadata from cache.'''
    new_task['metadata']['key'] = 'value'
    session.commit()

    fresh_session = ftrack_api.Session(cache=cache)

    # Prepare cache.
    fresh_session.query(
        'select metadata.key, metadata.value from '
        'Task where id is "{0}"'
        .format(new_task['id'])
    ).all()

    # Disable server calls.
    mocker.patch.object(fresh_session, '_call')

    # Retrieve entity from cache.
    entity = fresh_session.get(*ftrack_api.inspection.identity(new_task))

    assert entity is not None, 'Failed to retrieve entity from cache.'
    assert entity == new_task
    assert entity is not new_task

    # Check metadata cached correctly.
    with fresh_session.auto_populating(False):
        metadata = entity['metadata']
        assert metadata['key'] == 'value'

    assert not fresh_session._call.called
