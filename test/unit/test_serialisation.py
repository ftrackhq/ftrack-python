# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import textwrap

import pytest


def test_encode_entity_using_all_attributes_strategy(session, new_task):
    '''Encode entity using "all" entity_attribute_strategy.'''
    encoded = session.encode(
        new_task, entity_attribute_strategy='all'
    )

    assert encoded == textwrap.dedent('''
        {{"__entity_type__": "Task",
         "allocations": [],
         "appointments": [],
         "assignments": [],
         "bid": 0.0,
         "children": [],
         "context_type": "task",
         "description": "",
         "end_date": null,
         "id": "{0}",
         "metadata": [],
         "name": "{1}",
         "notes": [],
         "object_type": {{"__entity_type__": "ObjectType",
         "id": "11c137c0-ee7e-4f9c-91c5-8c77cec22b2c"}},
         "object_type_id": "11c137c0-ee7e-4f9c-91c5-8c77cec22b2c",
         "parent": {{"__entity_type__": "Project", "id":
         "5671dcb0-66de-11e1-8e6e-f23c91df25eb"}},
         "parent_id": "5671dcb0-66de-11e1-8e6e-f23c91df25eb",
         "priority": {{"__entity_type__": "PriorityType",
         "id": "34042886-58dc-11e2-93e8-f23c91df25eb"}},
         "priority_id": "34042886-58dc-11e2-93e8-f23c91df25eb",
         "project": {{"__entity_type__": "Project",
         "id": "5671dcb0-66de-11e1-8e6e-f23c91df25eb"}},
         "project_id": "5671dcb0-66de-11e1-8e6e-f23c91df25eb",
         "scopes": [],
         "sort": null,
         "start_date": null,
         "status": {{"__entity_type__": "TaskStatus",
         "id": "44dd9fb2-4164-11df-9218-0019bb4983d8"}},
         "status_id": "44dd9fb2-4164-11df-9218-0019bb4983d8",
         "timelogs": [],
         "type": {{"__entity_type__": "TaskType",
         "id": "44dbfca2-4164-11df-9218-0019bb4983d8"}},
         "type_id": "44dbfca2-4164-11df-9218-0019bb4983d8"}}
    '''.format(
        new_task['id'], new_task['name']
    )).replace('\n', '')


def test_encode_entity_using_only_set_attributes_strategy(
    session, new_task
):
    '''Encode entity using "set_only" entity_attribute_strategy.'''
    encoded = session.encode(
        new_task, entity_attribute_strategy='set_only'
    )

    assert encoded == textwrap.dedent('''
        {{"__entity_type__": "Task",
         "bid": 0.0,
         "context_type": "task",
         "description": "",
         "id": "{0}",
         "name": "{1}",
         "object_type_id": "11c137c0-ee7e-4f9c-91c5-8c77cec22b2c",
         "parent": {{"__entity_type__": "Project", "id":
         "5671dcb0-66de-11e1-8e6e-f23c91df25eb"}},
         "parent_id": "5671dcb0-66de-11e1-8e6e-f23c91df25eb",
         "priority": {{"__entity_type__": "PriorityType",
         "id": "34042886-58dc-11e2-93e8-f23c91df25eb"}},
         "priority_id": "34042886-58dc-11e2-93e8-f23c91df25eb",
         "project_id": "5671dcb0-66de-11e1-8e6e-f23c91df25eb",
         "status": {{"__entity_type__": "TaskStatus",
         "id": "44dd9fb2-4164-11df-9218-0019bb4983d8"}},
         "status_id": "44dd9fb2-4164-11df-9218-0019bb4983d8",
         "type": {{"__entity_type__": "TaskType",
         "id": "44dbfca2-4164-11df-9218-0019bb4983d8"}},
         "type_id": "44dbfca2-4164-11df-9218-0019bb4983d8"}}
    '''.format(
        new_task['id'], new_task['name']
    )).replace('\n', '')


def test_encode_entity_using_only_modified_attributes_strategy(
    session, new_task
):
    '''Encode entity using "modified_only" entity_attribute_strategy.'''
    new_task['name'] = 'Modified'

    encoded = session.encode(
        new_task, entity_attribute_strategy='modified_only'
    )

    assert encoded == textwrap.dedent('''
        {{"__entity_type__": "Task",
         "id": "{0}",
         "name": "Modified"}}
    '''.format(
        new_task['id']
    )).replace('\n', '')


def test_encode_entity_using_invalid_strategy(session, new_task):
    '''Fail to encode entity using invalid strategy.'''
    with pytest.raises(ValueError):
        session.encode(new_task, entity_attribute_strategy='invalid')


def test_decode_partial_entity(
    session, new_task
):
    '''Decode partially encoded entity.'''
    encoded = session.encode(
        new_task, entity_attribute_strategy='set_only'
    )

    entity = session.decode(encoded)

    assert entity == new_task
    assert entity is not new_task
