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


def test_set_custom_attribute_on_new_but_persisted_version(
    session, new_asset_version
):
    '''Set custom attribute on new persisted version.'''
    new_asset_version['custom_attributes']['versiontest'] = 5
    session.commit()
