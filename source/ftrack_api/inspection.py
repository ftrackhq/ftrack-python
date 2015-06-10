# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import collections

import ftrack_api.symbol
import ftrack_api.operation


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
        if value is ftrack_api.symbol.NOT_SET:
            raise KeyError(
                'Missing required value for primary key attribute "{0}" on '
                'entity {1!r}.'.format(name, entity)
            )

        primary_key[str(name)] = str(value)

    return primary_key


def state(entity):
    '''Return current *entity* state.

    .. seealso:: :func:`ftrack_api.inspection.states`.

    '''
    value = ftrack_api.symbol.NOT_SET

    # TODO: Optimise this.
    for operation in entity.session.recorded_operations:

        # Determine if operation refers to an entity and whether that entity
        # is this entity.
        if (
            isinstance(
                operation,
                (
                    ftrack_api.operation.CreateEntityOperation,
                    ftrack_api.operation.UpdateEntityOperation,
                    ftrack_api.operation.DeleteEntityOperation
                )
            )
            and operation.entity_type == entity.entity_type
            and operation.entity_key == primary_key(entity)
        ):

            if (
                isinstance(
                    operation, ftrack_api.operation.CreateEntityOperation
                )
                and value is ftrack_api.symbol.NOT_SET
            ):
                value = ftrack_api.symbol.CREATED

            elif (
                isinstance(
                    operation, ftrack_api.operation.UpdateEntityOperation
                )
                and value is ftrack_api.symbol.NOT_SET
            ):
                value = ftrack_api.symbol.MODIFIED

            elif isinstance(
                operation, ftrack_api.operation.DeleteEntityOperation
            ):
                value = ftrack_api.symbol.DELETED

    return value

