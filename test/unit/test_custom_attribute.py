# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import pytest


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

    entity['custom_attributes'][custom_attribute_name] = 'FOO'

    assert entity['custom_attributes'][custom_attribute_name] == 'FOO'

    session.commit()


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

    entity['custom_attributes'][custom_attribute_name] = 'FOO'

    assert entity['custom_attributes'][custom_attribute_name] == 'FOO'

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
        entity['custom_attributes'][custom_attribute_name] = 'FOO'


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
        'customNumber': 'Foo'
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
        'test_number': 'Foo'
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
