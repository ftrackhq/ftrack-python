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
            os.remove(cache_path)

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
    session._merge(task)

    # Disable server calls.
    mocker.patch.object(session, '_call')

    # Retrieve entity from cache.
    entity = session.get(*ftrack_api.inspection.identity(task))

    assert entity is not None, 'Failed to retrieve entity from cache.'
    assert entity == task
    assert entity is not task

    # Check that no call was made to server.
    assert not session._call.called


def test_get_entity_tree_from_cache(cache, new_project, mocker):
    '''Retrieve an entity tree from cache.'''
    session = ftrack_api.Session(cache=cache)

    # Prepare cache.
    # TODO: Maybe cache should be prepopulated for a better check here.
    session.query(
        'select children, children.children, children.children.children, '
        'children.children.children.assignments, '
        'children.children.children.assignments.resource '
        'from Project where id is "{0}"'
        .format(new_project['id'])
    )[0]

    # Disable server calls.
    mocker.patch.object(session, '_call')

    # Retrieve entity from cache.
    entity = session.get(*ftrack_api.inspection.identity(new_project))

    assert entity is not None, 'Failed to retrieve entity from cache.'
    assert entity == new_project
    assert entity is not new_project

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
