# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

from .base import Structure


class OriginStructure(Structure):
    '''Origin structure supporting Components only.

    Will maintain original internal component path.

    '''

    def get_resource_identifier(self, entity):
        '''Return a resource identifier for supplied *entity*.'''
        if entity.entity_type not in (
            'FileComponent', 'ContainerComponent', 'SequenceComponent'
        ):
            raise NotImplementedError('Cannot generate path for unsupported '
                                      'entity {0}'.format(entity))

        path = entity.get_resource_identifier()
        if path is None:
            raise ValueError('Could not generate path for component that has '
                             'no original path.')

        return path
