# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import pytest


@pytest.mark.parametrize(
    'entity_type,entity_id,custom_attribute_name,expected_value',
    [
        ('Task', '33cab460-9812-11e1-b87a-f23c91df25eb', 'customNumber', '213'),
        ('Shot', 'cb4bb98e-9811-11e1-b32d-f23c91df25eb', 'fstart', '8'),
        (
            'AssetVersion', 'e80fd79c-c5ea-11e1-94af-f23c91df25eb',
            'NumberField', '-5'
        )
    ],
    ids=[
        'task',
        'shot',
        'asset_version'
    ]
)
def test_read_set_custom_attribute(
    session, entity_type, entity_id, custom_attribute_name, expected_value
):
    '''Test retrieving a custom attribute.'''
    entity = session.query(
        'select custom_attributes from {entity_type} where id is'
        ' "{entity_id}"'.format(
            entity_type=entity_type, entity_id=entity_id
        )
    ).first()

    assert entity['id'] == entity['custom_attributes'].collection.entity['id']
    assert entity is entity['custom_attributes'].collection.entity
    assert entity['custom_attributes'][custom_attribute_name] == expected_value

    assert custom_attribute_name in entity['custom_attributes'].keys()


@pytest.mark.parametrize(
    'entity_type,entity_id,custom_attribute_name,expected_value',
    [
        ('Task', '33d56bee-9812-11e1-b87a-f23c91df25eb', 'customNumber', '123')
    ],
    ids=[
        'task'
    ]
)
def test_read_unset_custom_attribute(
    session, entity_type, entity_id, custom_attribute_name, expected_value
):
    '''Test retrieving a custom attribute.'''
    entity = session.query(
        'select custom_attributes from {entity_type} where id is'
        ' "{entity_id}"'.format(
            entity_type=entity_type, entity_id=entity_id
        )
    ).first()

    assert entity['id'] == entity['custom_attributes'].collection.entity['id']
    assert entity is entity['custom_attributes'].collection.entity
    assert entity['custom_attributes'][custom_attribute_name] == expected_value

    assert custom_attribute_name in entity['custom_attributes'].keys()


@pytest.mark.parametrize(
    'entity_type,entity_id,custom_attribute_name',
    [
        ('Task', '33cab460-9812-11e1-b87a-f23c91df25eb', 'customNumber'),
        ('Shot', 'cb4bb98e-9811-11e1-b32d-f23c91df25eb', 'fstart'),
        (
            'AssetVersion', 'e80fd79c-c5ea-11e1-94af-f23c91df25eb',
            'NumberField'
        )
    ],
    ids=[
        'task',
        'shot',
        'asset_version'
    ]
)
def test_write_set_custom_attribute_value(
    session, entity_type, entity_id, custom_attribute_name
):
    '''Test writing a set custom attribute value.'''
    entity = session.query(
        'select custom_attributes from {entity_type} where id is'
        ' "{entity_id}"'.format(
            entity_type=entity_type, entity_id=entity_id
        )
    ).first()

    entity['custom_attributes'][custom_attribute_name] = 'FOO'

    assert entity['custom_attributes'][custom_attribute_name] == 'FOO'


@pytest.mark.parametrize(
    'entity_type,entity_id,custom_attribute_name',
    [
        ('Task', '33cab460-9812-11e1-b87a-f23c91df25eb', 'customDate')
    ],
    ids=[
        'task'
    ]
)
def test_write_unset_custom_attribute_value(
    session, entity_type, entity_id, custom_attribute_name
):
    '''Test writing an unset custom attribute value.'''
    entity = session.query(
        'select custom_attributes from {entity_type} where id is'
        ' "{entity_id}"'.format(
            entity_type=entity_type, entity_id=entity_id
        )
    ).first()

    entity['custom_attributes'][custom_attribute_name] = 'FOO'

    assert entity['custom_attributes'][custom_attribute_name] == 'FOO'


@pytest.mark.parametrize(
    'entity_type,entity_id,custom_attribute_name',
    [
        ('Task', '33cab460-9812-11e1-b87a-f23c91df25eb', 'fstart'),
        ('Shot', 'cb4bb98e-9811-11e1-b32d-f23c91df25eb', 'Not existing'),
        (
            'AssetVersion', 'e80fd79c-c5ea-11e1-94af-f23c91df25eb',
            'fstart'
        )
    ],
    ids=[
        'task',
        'shot',
        'asset_version'
    ]
)
def test_read_custom_attribute_that_does_not_exist(
    session, entity_type, entity_id, custom_attribute_name
):
    entity = session.query(
        'select custom_attributes from {entity_type} where id is'
        ' "{entity_id}"'.format(
            entity_type=entity_type, entity_id=entity_id
        )
    ).first()

    with pytest.raises(KeyError):
        entity['custom_attributes'][custom_attribute_name]


@pytest.mark.parametrize(
    'entity_type,entity_id,custom_attribute_name',
    [
        ('Task', '33cab460-9812-11e1-b87a-f23c91df25eb', 'fstart'),
        ('Shot', 'cb4bb98e-9811-11e1-b32d-f23c91df25eb', 'Not existing'),
        (
            'AssetVersion', 'e80fd79c-c5ea-11e1-94af-f23c91df25eb',
            'fstart'
        )
    ],
    ids=[
        'task',
        'shot',
        'asset_version'
    ]
)
def test_write_custom_attribute_that_does_not_exist(
    session, entity_type, entity_id, custom_attribute_name
):
    entity = session.query(
        'select custom_attributes from {entity_type} where id is'
        ' "{entity_id}"'.format(
            entity_type=entity_type, entity_id=entity_id
        )
    ).first()

    with pytest.raises(KeyError):
        entity['custom_attributes'][custom_attribute_name] = 'FOO'


@pytest.mark.parametrize(
    'entity_type,entity_id,custom_attribute_name',
    [
        ('Task', '33cab460-9812-11e1-b87a-f23c91df25eb', 'customNumber'),
        ('Task', '33cab460-9812-11e1-b87a-f23c91df25eb', 'customDate')
    ],
    ids=[
        'task_with_set_custom_attribute',
        'task_with_unset_custom_attribute'
    ]
)
def test_owerwrite_custom_attributes_with_dictionary(
    session, entity_type, entity_id, custom_attribute_name
):
    '''Successfully overwrite custom attributes with a dictionary.'''
    entity = session.query(
        'select custom_attributes from {entity_type} where id is'
        ' "{entity_id}"'.format(
            entity_type=entity_type, entity_id=entity_id
        )
    ).first()

    entity['custom_attributes'] = {
        custom_attribute_name: 'Foo'
    }
