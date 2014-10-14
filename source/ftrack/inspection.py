# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import ftrack.symbol


def identity(entity):
    '''Return identity of *entity*.'''
    return (
        entity_type(entity),
        primary_key(entity)
    )


def entity_type(entity):
    '''Return entity type of *entity*.'''
    # Should this actually use the schema name?
    return str(type(entity).__name__)


def primary_key(entity, schema=None):
    '''Return primary key of *entity* according to *schema*.

    If *schema* is not passed, attempt to access 'schema' as a property of the
    passed *entity*.

    '''
    if schema is None:
        schema = entity.schema

    primary_key_definition = schema['primary_key']

    primary_key_value = []
    for key in primary_key_definition:
        value = entity[key]
        if value is ftrack.symbol.NOT_SET:
            raise KeyError(
                'Missing required value for primary key attribute "{0}" on '
                'entity {1}.'.format(key, entity)
            )

        primary_key_value.append(str(entity[key]))

    return tuple(primary_key_value)
