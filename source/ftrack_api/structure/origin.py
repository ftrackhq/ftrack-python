# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

from .base import Structure


class OriginStructure(Structure):
    '''Origin structure that passes through existing resource identifier.'''

    def get_resource_identifiers(self, entities, context=None):
        '''Return a resource identifier for supplied *entities*.

        *context* should be a mapping that includes at least a
        'source_resource_identifier' key that refers to the resource identifier
        to pass through.

        '''
        if context is None:
            context = {}

        result = []

        for entity in entities:
            resource_identifier = context.get('source_resource_identifier')
            if resource_identifier is None:
                raise ValueError(
                    'Could not generate resource identifier as no source resource '
                    'identifier found in passed context.'
                )
            result.append(resource_identifier)

        return result
