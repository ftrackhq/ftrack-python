# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import pytest
import json

@pytest.mark.parametrize(
    'entity_type, entity_model_name, custom_attribute_name',
    [
        ('Task', 'task', 'customNumber'),
        ('Shot', 'task', 'fstart'),
        ('AssetVersion', 'assetversion', 'NumberField')
    ],
    ids=[
        'task',
        'shot',
        'asset_version'
    ]
)
def test_read_set_custom_attribute(
    session, entity_type, entity_model_name, custom_attribute_name
):
    '''Retrieve custom attribute value set on instance.'''
    entity = session.query(
        'select custom_attributes from {entity_type} where '
        'custom_attributes.configuration.key is {custom_attribute_name}'.format(
            entity_type=entity_type,
            custom_attribute_name=custom_attribute_name
        )
    ).first()

    custom_attribute_value = session.query(
        'CustomAttributeValue where entity_id is {entity_id} and '
        'configuration.key is {custom_attribute_name}'.format(
            entity_id=entity['id'],
            custom_attribute_name=custom_attribute_name
        )
    ).first()

    assert entity['id'] == entity['custom_attributes'].collection.entity['id']
    assert entity is entity['custom_attributes'].collection.entity
    assert (
        entity['custom_attributes'][custom_attribute_name] ==
        custom_attribute_value['value']
    )

    assert custom_attribute_name in entity['custom_attributes'].keys()


@pytest.mark.parametrize(
    'entity_type, entity_model_name, custom_attribute_name',
    [
        ('Shot', 'task', 'fstart'),
        ('AssetVersion', 'assetversion', 'versiontest')
    ],
    ids=[
        'shot',
        'asset_version'
    ]
)
def test_read_unset_custom_attribute(
    session, entity_type, entity_model_name, custom_attribute_name
):
    '''Retrieve custom attribute default value when not set on instance.'''
    configuration = session.query(
        'select default from CustomAttributeConfiguration where key is '
        '{custom_attribute_name}'.format(
            custom_attribute_name=custom_attribute_name
        )
    ).first()
    expected_value = configuration['default']

    entity = session.query(
        'select custom_attributes from {entity_type} where '
        'not custom_attributes any ()'.format(
            entity_type=entity_type,
            custom_attribute_name=custom_attribute_name
        )
    ).first()

    assert entity['id'] == entity['custom_attributes'].collection.entity['id']
    assert entity is entity['custom_attributes'].collection.entity
    assert entity['custom_attributes'][custom_attribute_name] == expected_value

    assert custom_attribute_name in entity['custom_attributes'].keys()


@pytest.mark.parametrize(
    'entity_type, custom_attribute_name',
    [
        ('Task', 'customNumber'),
        ('Shot', 'fstart'),
        (
            'AssetVersion', 'NumberField'
        )
    ],
    ids=[
        'task',
        'shot',
        'asset_version'
    ]
)
def test_write_set_custom_attribute_value(
    session, entity_type, custom_attribute_name
):
    '''Overwrite existing instance level custom attribute value.'''
    entity = session.query(
        'select custom_attributes from {entity_type} where '
        'custom_attributes.configuration.key is {custom_attribute_name}'.format(
            entity_type=entity_type,
            custom_attribute_name=custom_attribute_name
        )
    ).first()

    entity['custom_attributes'][custom_attribute_name] = 42

    assert entity['custom_attributes'][custom_attribute_name] == 42

    session.commit()


@pytest.mark.parametrize(
    'entity_type, entity_model_name, custom_attribute_name',
    [
        ('Shot', 'task', 'fstart')
    ],
    ids=[
        'shot'
    ]
)
def test_write_unset_custom_attribute_value(
    session, entity_type, entity_model_name, custom_attribute_name
):
    '''Set instance level custom attribute value for first time.'''
    entity = session.query(
        'select custom_attributes from {entity_type} where '
        'not custom_attributes any ()'.format(
            entity_type=entity_type,
            custom_attribute_name=custom_attribute_name
        )
    ).first()

    entity['custom_attributes'][custom_attribute_name] = 42

    assert entity['custom_attributes'][custom_attribute_name] == 42

    session.commit()


@pytest.mark.parametrize(
    'entity_type, custom_attribute_name',
    [
        ('Task', 'fstart'),
        ('Shot', 'Not existing'),
        ('AssetVersion', 'fstart')
    ],
    ids=[
        'task',
        'shot',
        'asset_version'
    ]
)
def test_read_custom_attribute_that_does_not_exist(
    session, entity_type, custom_attribute_name
):
    '''Fail to read value from a custom attribute that does not exist.'''
    entity = session.query(
        'select custom_attributes from {entity_type}'.format(
            entity_type=entity_type
        )
    ).first()

    with pytest.raises(KeyError):
        entity['custom_attributes'][custom_attribute_name]


@pytest.mark.parametrize(
    'entity_type, custom_attribute_name',
    [
        ('Task', 'fstart'),
        ('Shot', 'Not existing'),
        ('AssetVersion', 'fstart')
    ],
    ids=[
        'task',
        'shot',
        'asset_version'
    ]
)
def test_write_custom_attribute_that_does_not_exist(
    session, entity_type, custom_attribute_name
):
    '''Fail to write a value to a custom attribute that does not exist.'''
    entity = session.query(
        'select custom_attributes from {entity_type}'.format(
            entity_type=entity_type
        )
    ).first()

    with pytest.raises(KeyError):
        entity['custom_attributes'][custom_attribute_name] = 42


def test_update_custom_attributes_with_dictionary_when_set(session):
    '''Batch set custom attribute values when set on instance'''
    configuration = session.query(
        'CustomAttributeConfiguration where key is customNumber'
    ).first()

    entity = session.query(
        'select custom_attributes from Task where '
        'custom_attributes.configuration.key is customNumber and '
        'project_id is {project_id}'.format(
            project_id=configuration['project_id']
        )
    ).first()

    entity['custom_attributes'] = {
        'customNumber': 42
    }

    session.commit()


def test_update_custom_attributes_with_dictionary_when_unset(session):
    '''Batch set custom attribute values when not set on instance.'''
    configuration = session.query(
        'CustomAttributeConfiguration where key is test_number'
    ).first()

    entity = session.query(
        'select custom_attributes from Task where '
        'not custom_attributes any () and '
        'project_id is {project_id}'.format(
            project_id=configuration['project_id']
        )
    ).first()

    entity['custom_attributes'] = {
        'test_number': 42
    }

    session.commit()


def test_write_non_existing_custom_attributes_with_dictionary(session):
    '''Fail to batch set values for missing custom attribute.'''
    entity = session.query(
        'select custom_attributes from Shot'
    ).first()

    with pytest.raises(KeyError):
        entity['custom_attributes'] = {
            'BAZ': 'Foo'
        }


def test_set_custom_attribute_on_new_but_persisted_version(
    session, new_asset_version
):
    '''Set custom attribute on new persisted version.'''
    new_asset_version['custom_attributes']['versiontest'] = 5
    session.commit()


@pytest.mark.xfail
def test_enumerator_custom_attribute_caching(
    session, new_asset_version
):
    '''Set custom attribute of enumerator values.

    Sets the value to one, and then another value to ensure caching is
    properly cleared.
    '''
    configuration = session.query(
        'select object_type_id, project_id, key, config '
        'from CustomAttributeConfiguration '
        'where type.name is Enumerator and entity_type is task'
    ).first()
    attribute_key = configuration['key']

    entity = session.query(
        'select custom_attributes from TypedContext '
        'where object_type_id is "{}" and project_id is "{}"'.format(
            configuration['object_type_id'], configuration['project_id']
        )
    ).first()
    original_value = entity['custom_attributes'][attribute_key]

    # Get a valid option from all possible enumerator values
    possible_values = [
        option['value']
        for option in json.loads(
            json.loads(configuration['config'])['data']
        )
    ]
    test_value = [possible_values[0]]

    # Set custom attribute to first value, commit and assert
    entity['custom_attributes'][attribute_key] = []
    session.commit()
    assert entity['custom_attributes'][attribute_key] == []

    # Set the custom attribute to a second value.
    # An issue currently prevents the value from being persisted properly.
    entity['custom_attributes'][attribute_key] = test_value
    assert entity['custom_attributes'][attribute_key] == test_value
    session.commit()
    # TODO: This assertion should hold true, the attribute has currently been reverted.
    assert entity['custom_attributes'][attribute_key] == test_value

    # Revert original value
    entity['custom_attributes'][attribute_key] = original_value
    session.commit()
