# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import os

import ftrack_api.symbol
import ftrack_api.structure.base

from collections import OrderedDict

class IdStructure(ftrack_api.structure.base.Structure):
    ''' Id based structures.

    A components or entity unique id will be used to form a path to store the data at.
    To avoid millions of entries in one directory each id is chunked into four
    prefix directories with the remainder used to name the file::

        /prefix/1/2/3/4/56789

    If the component has a defined filetype it will be added to the path::

        /prefix/1/2/3/4/56789.exr

    Components that are children of container components will be placed inside
    the id structure of their parent::

        /prefix/1/2/3/4/56789/355827648d.exr
        /prefix/1/2/3/4/56789/ajf24215b5.exr

    However, sequence children will be named using their label as an index and
    a common prefix of 'file.'::

        /prefix/1/2/3/4/56789/file.0001.exr
        /prefix/1/2/3/4/56789/file.0002.exr

    '''
    def __init__(self, prefix=''):
        super(IdStructure, self).__init__(prefix=prefix)
        self.resolvers = OrderedDict({
            'FileComponent': self._resolve_file_component,
            'SequenceComponent': self._resolve_sequence_component,
            'ContainerComponent': self._resolve_container_component,
            'ContextEntity': self._resolve_context_entity
        })

    def _get_id_folder(self, id):
        '''Generate a folder name based on **id.'''
        parts = [self.prefix]
        parts.extend(list(id[:4]))
        return parts

    def _resolve_context_entity(self, entity, context=None):
        '''Return if resource identifier parts from general *entity*.'''

        # Not an component, base on its id - all types of entities allowed
        if not 'id' in entity:
            raise NotImplementedError('Cannot generate resource identifier'
                                      ' for unsupported entity {0}'.format(
                entity))
        parts = (self._get_id_folder(entity['id']) + [entity['id'][4:]])
        return parts


    def _resolve_sequence_component(self, sequence_component, context=None):
        '''Get id resource identifier for *sequence_component*.'''
        name = 'file'

        # Add a sequence identifier.
        sequence_expression = self._get_sequence_expression(sequence_component)
        name += '.{0}'.format(sequence_expression)

        if (
                sequence_component['file_type'] and
                sequence_component['file_type'] is not ftrack_api.symbol.NOT_SET
        ):
            name += sequence_component['file_type']

        parts = (self._get_id_folder(sequence_component['id'])
            + [sequence_component['id'][4:]]
            + [name])

        return parts


    def _resolve_file_component(self, file_component, context=None):
        '''Get id resource identifier for *file_component*.'''
        # When in a container, place the file inside a directory named
        # after the container.
        container = file_component['container']
        if container and container is not ftrack_api.symbol.NOT_SET:
            path = self.get_resource_identifier(container)

            if container.entity_type in ('SequenceComponent',):
                # Label doubles as index for now.
                name = 'file.{0}{1}'.format(
                    file_component['name'], file_component['file_type']
                )
                parts = [os.path.dirname(path), name]

            else:
                # Just place uniquely identified file into directory
                name = file_component['id'] + file_component['file_type']
                parts = [path, name]

        else:
            name = file_component['id'][4:] + file_component['file_type']
            parts = (self._get_id_folder(file_component['id']) + [name])

        return parts

    def _resolve_container_component(self, container_component, context=None):
        '''Get id resource identifier for *container_component*.'''
        # Just an id directory
        parts = (self._get_id_folder(container_component['id'])
            + [container_component['id'][4:]])
        return parts

    def get_resource_identifier(self, entity, context=None):
        '''Return a resource identifier for supplied *entity*.

        *context* can be a mapping that supplies additional information, but
        is unused in this implementation.


        Raise a :py:exc:`ftrack_api.exeption.StructureError` if *entity* is not
        attached to a committed version and a committed asset with a parent
        context.

        '''

        resolver_fn = self.resolvers.get(entity.entity_type,
                                         self._resolve_context_entity)

        parts = resolver_fn(entity, context=context)

        return self.path_separator.join(parts).strip('/')
