# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import textwrap

import pytest


def test_encode_entity_using_all_attributes_strategy(session, new_user):
    '''Encode entity using "all" entity_attribute_strategy.'''
    encoded = session.encode(
        new_user, entity_attribute_strategy='all'
    )

    assert encoded == textwrap.dedent('''
        {{"__entity_type__": "User",
         "allocations": [],
         "appointments": [],
         "assignments": [],
         "email": null,
         "first_name": "first",
         "id": "{0}",
         "is_active": false,
         "last_name": "last",
         "resource_type": "user",
         "timelogs": [],
         "username": "{1}"}}
    '''.format(
        new_user['id'], new_user['username']
    )).replace('\n', '')


def test_encode_entity_using_only_set_attributes_strategy(
    session, new_user
):
    '''Encode entity using "set_only" entity_attribute_strategy.'''
    encoded = session.encode(
        new_user, entity_attribute_strategy='set_only'
    )

    assert encoded == textwrap.dedent('''
        {{"__entity_type__": "User",
         "first_name": "first",
         "id": "{0}",
         "is_active": false,
         "last_name": "last",
         "resource_type": "user",
         "username": "{1}"}}
    '''.format(
        new_user['id'], new_user['username']
    )).replace('\n', '')


def test_encode_entity_using_only_modified_attributes_strategy(
    session, new_user
):
    '''Encode entity using "modified_only" entity_attribute_strategy.'''
    new_user['first_name'] = 'Modified'

    encoded = session.encode(
        new_user, entity_attribute_strategy='modified_only'
    )

    assert encoded == textwrap.dedent('''
        {{"__entity_type__": "User",
         "first_name": "Modified",
         "id": "{0}"}}
    '''.format(
        new_user['id']
    )).replace('\n', '')


def test_encode_entity_using_invalid_strategy(session, new_user):
    '''Fail to encode entity using invalid strategy.'''
    with pytest.raises(ValueError):
        session.encode(new_user, entity_attribute_strategy='invalid')


def test_decode_partial_entity(
    session, new_user
):
    '''Decode partially encoded entity.'''
    encoded = session.encode(
        new_user, entity_attribute_strategy='set_only'
    )

    entity = session.decode(encoded)

    assert entity == new_user
    assert entity is not new_user
