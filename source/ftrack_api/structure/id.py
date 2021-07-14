# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import os

import ftrack_api.symbol
import ftrack_api.structure.base


class IdStructure(ftrack_api.structure.base.Structure):
    '''Id based structures.

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

    def _get_id_folder(self, id):
        parts = [self.prefix]
        parts.extend(list(id[:4]))
        return parts

    def get_resource_identifiers(self, entities, context=None):
        '''Return a resource identifier for supplied *entities*.

        *context* can be a mapping that supplies additional information.

        '''
        result = []
        for entity in entities:
            if entity.entity_type in ('FileComponent',):
                # When in a container, place the file inside a directory named
                # after the container.
                container = entity['container']
                if container and container is not ftrack_api.symbol.NOT_SET:
                    path = self.get_resource_identifier(container)

                    if container.entity_type in ('SequenceComponent',):
                        # Label doubles as index for now.
                        name = 'file.{0}{1}'.format(
                            entity['name'], entity['file_type']
                        )
                        parts = [os.path.dirname(path), name]

                    else:
                        # Just place uniquely identified file into directory
                        name = entity['id'] + entity['file_type']
                        parts = [path, name]

                else:
                    name = entity['id'][4:] + entity['file_type']
                    parts = (self._get_id_folder(entity['id']) + [name])

            elif entity.entity_type in ('SequenceComponent',):
                name = 'file'

                # Add a sequence identifier.
                sequence_expression = self._get_sequence_expression(entity)
                name += '.{0}'.format(sequence_expression)

                if (
                    entity['file_type'] and
                    entity['file_type'] is not ftrack_api.symbol.NOT_SET
                ):
                    name += entity['file_type']

                parts = (self._get_id_folder(entity['id']) + [entity['id'][4:]]
                         + [name])

            elif entity.entity_type in ('ContainerComponent',):
                # Just an id directory
                parts = (self._get_id_folder(entity['id']) + [entity['id'][4:]])

            else:
                # Not an component, base on its id - all types of entities allowed
                if not 'id' in entity:
                    raise NotImplementedError('Cannot generate resource identifier'
                                              ' for unsupported entity {0}'.format(
                        entity))
                parts = (self._get_id_folder(entity['id']) + [entity['id'][4:]])

            result.append(self.path_separator.join(parts).strip('/'))

        return result
