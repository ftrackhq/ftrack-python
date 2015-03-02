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
         "metadata": {{}},
         "name": "{1}",
         "object_type": {{"__entity_type__": "ObjectType",
         "id": "11c137c0-ee7e-4f9c-91c5-8c77cec22b2c"}},
         "object_type_id": "11c137c0-ee7e-4f9c-91c5-8c77cec22b2c",
         "parent": {{"__entity_type__": "Project", "id":
         "046a715c-12e8-4e5e-9536-29a3a93d6ee1"}},
         "parent_id": "046a715c-12e8-4e5e-9536-29a3a93d6ee1",
         "priority": {{"__entity_type__": "PriorityType",
         "id": "34042886-58dc-11e2-93e8-f23c91df25eb"}},
         "priority_id": "34042886-58dc-11e2-93e8-f23c91df25eb",
         "project": {{"__entity_type__": "Project",
         "id": "046a715c-12e8-4e5e-9536-29a3a93d6ee1"}},
         "project_id": "046a715c-12e8-4e5e-9536-29a3a93d6ee1",
         "scopes": [],
         "sort": null,
         "start_date": null,
         "status": {{"__entity_type__": "TaskStatus",
         "id": "e610b180-4e64-11e1-a500-f23c91df25eb"}},
         "status_id": "e610b180-4e64-11e1-a500-f23c91df25eb",
         "timelogs": [],
         "type": {{"__entity_type__": "TaskType",
         "id": "400b856c-4e64-11e1-b8af-f23c91df25eb"}},
         "type_id": "400b856c-4e64-11e1-b8af-f23c91df25eb",
         "workload": 100}}
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
         "metadata": {{}},
         "name": "{1}",
         "object_type_id": "11c137c0-ee7e-4f9c-91c5-8c77cec22b2c",
         "parent": {{"__entity_type__": "Project", "id":
         "046a715c-12e8-4e5e-9536-29a3a93d6ee1"}},
         "parent_id": "046a715c-12e8-4e5e-9536-29a3a93d6ee1",
         "priority": {{"__entity_type__": "PriorityType",
         "id": "34042886-58dc-11e2-93e8-f23c91df25eb"}},
         "priority_id": "34042886-58dc-11e2-93e8-f23c91df25eb",
         "project_id": "046a715c-12e8-4e5e-9536-29a3a93d6ee1",
         "status": {{"__entity_type__": "TaskStatus",
         "id": "e610b180-4e64-11e1-a500-f23c91df25eb"}},
         "status_id": "e610b180-4e64-11e1-a500-f23c91df25eb",
         "type": {{"__entity_type__": "TaskType",
         "id": "400b856c-4e64-11e1-b8af-f23c91df25eb"}},
         "type_id": "400b856c-4e64-11e1-b8af-f23c91df25eb",
         "workload": 100}}
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
