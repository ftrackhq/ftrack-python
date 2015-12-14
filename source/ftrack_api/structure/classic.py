# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os

import ftrack_api.structure.base


class ClassicStructure(ftrack_api.structure.base.Structure):
    '''Project hierarchy based structure that only supports Components.

    The resource identifier is generated from the project code, the name
    objects in the project structure, asset name and version number::

        my_project/folder_a/folder_b/asset_name/v003

    If the component is a `FileComponent` the name of the component and the
    file type are used as filename in the resource_identifier::

        my_project/folder_a/folder_b/asset_name/v003/foo.jpg

    If the component is a `SequenceComponent` a sequence expression, `%04d`, is
    used. E.g. a component with the name `foo` yields::

        my_project/folder_a/folder_b/asset_name/v003/foo.%04d.jpg

    For the member components their index in the sequence are used::

        my_project/folder_a/folder_b/asset_name/v003/foo.0042.jpg

    The name of the component is added to the resource identifier if the
    component is a `ContainerComponent`. E.g. a container component with the
    name `bar` yields::

        my_project/folder_a/folder_b/asset_name/v003/bar

    For a member the file name is based on the component name and file type::

        my_project/folder_a/folder_b/asset_name/v003/bar/baz.pdf

    If set *project_versions_prefix* will be added used for versions published
    directly under the projcet::

        my_project/**project_versions_prefix*/v001/foo.jpg

    .. note::

        Nested component containers/sequences are not supported.

    '''

    def __init__(self, project_versions_prefix=None):
        '''Instantiate structure with *project_versions_prefix*.'''
        super(ClassicStructure, self).__init__()
        self.project_versions_prefix = project_versions_prefix

    def _get_parts(self, entity):
        '''Return resource identifier parts from *entity*.'''
        session = entity.session
        component = session.query(
            'Component where id is "{0}"'.format(
                entity['id']
            )
        ).one()

        structure_names = [
            item['name']
            for item in component['version']['link'][1:-1]
        ]

        project_id = component['version']['link'][0]['id']
        project = session.get('Project', project_id)
        asset = component['version']['asset']

        version_number = 'v{0:03d}'.format(component['version']['version'])

        parts = []
        parts.append(project['name'])
        parts.extend(structure_names)
        parts.append(asset['name'])
        parts.append(version_number)

        return parts

    def get_resource_identifier(self, entity, context=None):
        '''Return a resource identifier for supplied *entity*.

        *context* can be a mapping that supplies additional information.

        '''
        if entity.entity_type in ('FileComponent',):
            container = entity['container']

            if container and container is not ftrack_api.symbol.NOT_SET:
                container_path = self.get_resource_identifier(container)

                if container.entity_type in ('SequenceComponent',):
                    name = '{0}.{1}{2}'.format(
                        container['name'], entity['name'], entity['file_type']
                    )
                    parts = [
                        os.path.dirname(container_path), name
                    ]

                else:
                    name = entity['name'] + entity['file_type']
                    parts = [
                        container_path, name
                    ]

            else:
                parts = self._get_parts(entity)
                name = entity['name'] + entity['file_type']
                parts.append(name)

        elif entity.entity_type in ('SequenceComponent',):
            parts = self._get_parts(entity)
            sequence_expression = self._get_sequence_expression(entity)
            parts.append(
                '{}.{}{}'.format(
                    entity['name'], sequence_expression,
                    entity['file_type']
                )
            )

        elif entity.entity_type in ('ContainerComponent',):
            parts = self._get_parts(entity)

        else:
            raise NotImplementedError(
                'Cannot generate resource identifier for unsupported '
                'entity {0!r}'.format(entity)
            )

        resource_identifier = self.path_separator.join(
            parts
        ).replace(' ', '_').lower()

        return resource_identifier
