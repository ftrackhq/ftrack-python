# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import textwrap

import pytest


def test_encode_entity_using_all_attributes_strategy(session, unique_entity):
    '''Encode entity using "all" entity_attribute_strategy.'''
    encoded = session.encode(
        unique_entity, entity_attribute_strategy='all'
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
        unique_entity['id'], unique_entity['username']
    )).replace('\n', '')


def test_encode_entity_using_only_set_attributes_strategy(
    session, unique_entity
):
    '''Encode entity using "set_only" entity_attribute_strategy.'''
    encoded = session.encode(
        unique_entity, entity_attribute_strategy='set_only'
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
        unique_entity['id'], unique_entity['username']
    )).replace('\n', '')


def test_encode_entity_using_only_modified_attributes_strategy(
    session, unique_entity
):
    '''Encode entity using "modified_only" entity_attribute_strategy.'''
    unique_entity['first_name'] = 'Modified'

    encoded = session.encode(
        unique_entity, entity_attribute_strategy='modified_only'
    )

    assert encoded == textwrap.dedent('''
        {{"__entity_type__": "User",
         "first_name": "Modified",
         "id": "{0}"}}
    '''.format(
        unique_entity['id']
    )).replace('\n', '')


def test_encode_entity_using_invalid_strategy(session, unique_entity):
    '''Fail to encode entity using invalid strategy.'''
    with pytest.raises(ValueError):
        session.encode(unique_entity, entity_attribute_strategy='invalid')


def test_decode_partial_entity(
    session, unique_entity
):
    '''Decode partially encoded entity.'''
    encoded = session.encode(
        unique_entity, entity_attribute_strategy='set_only'
    )

    entity = session.decode(encoded)

    assert entity == unique_entity
    assert entity is not unique_entity
