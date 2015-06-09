# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import ftrack_api.symbol


def test_created_entity_state(session, unique_name):
    '''Created entity has CREATED state.'''
    new_user = session.create('User', {'username': unique_name})
    assert new_user.state is ftrack_api.symbol.CREATED

    # Even after a modification the state should remain as CREATED.
    new_user['username'] = 'changed'
    assert new_user.state is ftrack_api.symbol.CREATED


def test_retrieved_entity_state(user):
    '''Retrieved entity has NOT_SET state.'''
    assert user.state is ftrack_api.symbol.NOT_SET


def test_modified_entity_state(user):
    '''Modified entity has MODIFIED state.'''
    user['username'] = 'changed'
    assert user.state is ftrack_api.symbol.MODIFIED


def test_deleted_entity_state(session, user):
    '''Deleted entity has DELETED state.'''
    session.delete(user)
    assert user.state is ftrack_api.symbol.DELETED
