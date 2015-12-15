# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import re
import unicodedata

import ftrack_api.structure.base


class StandardStructure(ftrack_api.structure.base.Structure):
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

    Add *project_versions_prefix* for versions published directly under the
    project if set::

        my_project/**project_versions_prefix*/v001/foo.jpg

    Replace illegal characters with *replace_illegal_characters* if not None.

    .. note::

        Nested component containers/sequences are not supported.

    '''

    def __init__(
        self, project_versions_prefix=None, replace_illegal_characters='_'
    ):
        '''Instantiate structure with *project_versions_prefix*.'''
        super(StandardStructure, self).__init__()
        self.project_versions_prefix = project_versions_prefix
        self.replace_illegal_characters = replace_illegal_characters

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

        if structure_names:
            parts.extend(structure_names)
        elif self.project_versions_prefix:
            # Add *project_versions_prefix* if configured and the version is
            # published directly under the project.
            parts.append(self.project_versions_prefix)

        parts.append(asset['name'])
        parts.append(version_number)

        return [self.slugify(part) for part in parts]

    def slugify(self, value):
        '''Replace illegal file system characters in *value*.

        Illegal characters will be replaced with the
        *replace_illegal_characters* argument used when instantiating the
        structure.

        Illegal characters will not be replaced if StandardStructure is
        configured with a replace_illegal_characters equal to None.

        '''
        if self.replace_illegal_characters is None:
            return value

        if isinstance(value, str):
            value = value.decode('utf-8')

        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
        value = re.sub('[^\w\.-]', self.replace_illegal_characters, value)
        return unicode(value.strip().lower())

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
                        os.path.dirname(container_path), self.slugify(name)
                    ]

                else:
                    name = entity['name'] + entity['file_type']
                    parts = [
                        container_path, self.slugify(name)
                    ]

            else:
                parts = self._get_parts(entity)
                name = entity['name'] + entity['file_type']
                parts.append(self.slugify(name))

        elif entity.entity_type in ('SequenceComponent',):
            parts = self._get_parts(entity)
            sequence_expression = self._get_sequence_expression(entity)
            parts.append(
                '{}.{}{}'.format(
                    self.slugify(entity['name']), sequence_expression,
                    self.slugify(entity['file_type'])
                )
            )

        elif entity.entity_type in ('ContainerComponent',):
            parts = self._get_parts(entity)
            parts.append(self.slugify(entity['name']))

        else:
            raise NotImplementedError(
                'Cannot generate resource identifier for unsupported '
                'entity {0!r}'.format(entity)
            )

        return self.path_separator.join(
            parts
        )
