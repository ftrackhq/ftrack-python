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
    return entity.entity_type


def primary_key(entity):
    '''Return primary key of *entity*.'''
    primary_key_definition = entity.primary_key

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
