# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import collections

import ftrack.symbol


def identity(entity):
    '''Return unique identity of *entity*.'''
    return (
        str(entity.entity_type),
        primary_key(entity).values()
    )


def primary_key(entity):
    '''Return primary key of *entity* as an ordered mapping of {field: value}.

    To get just the primary key values::

        primary_key(entity).values()

    '''
    primary_key = collections.OrderedDict()
    for name in entity.primary_key_attributes:
        value = entity[name]
        if value is ftrack.symbol.NOT_SET:
            raise KeyError(
                'Missing required value for primary key attribute "{0}" on '
                'entity {1}.'.format(name, entity)
            )

        primary_key[str(name)] = str(value)

    return primary_key
