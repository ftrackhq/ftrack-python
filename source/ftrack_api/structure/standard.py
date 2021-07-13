# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

from builtins import str
import os
import re
import unicodedata

import ftrack_api.symbol
import ftrack_api.structure.base


class StandardStructure(ftrack_api.structure.base.Structure):
    '''Project hierarchy based structure that only supports Components.

    The resource identifier is generated from the project code, the name
    of objects in the project structure, asset name and version number::

        my_project/folder_a/folder_b/asset_name/v003

    If the component is a `FileComponent` then the name of the component and the
    file type are used as filename in the resource_identifier::

        my_project/folder_a/folder_b/asset_name/v003/foo.jpg

    If the component is a `SequenceComponent` then a sequence expression,
    `%04d`, is used. E.g. a component with the name `foo` yields::

        my_project/folder_a/folder_b/asset_name/v003/foo.%04d.jpg

    For the member components their index in the sequence is used::

        my_project/folder_a/folder_b/asset_name/v003/foo.0042.jpg

    The name of the component is added to the resource identifier if the
    component is a `ContainerComponent`. E.g. a container component with the
    name `bar` yields::

        my_project/folder_a/folder_b/asset_name/v003/bar

    For a member of that container the file name is based on the component name
    and file type::

        my_project/folder_a/folder_b/asset_name/v003/bar/baz.pdf

    '''

    def __init__(
        self, project_versions_prefix=None, illegal_character_substitute='_'
    ):
        '''Initialise structure.

        If *project_versions_prefix* is defined, insert after the project code
        for versions published directly under the project::

            my_project/<project_versions_prefix>/v001/foo.jpg

        Replace illegal characters with *illegal_character_substitute* if
        defined.

        .. note::

            Nested component containers/sequences are not supported.

        '''
        super(StandardStructure, self).__init__()
        self.project_versions_prefix = project_versions_prefix
        self.illegal_character_substitute = illegal_character_substitute

    def sanitise_for_filesystem(self, value):
        '''Return *value* with illegal filesystem characters replaced.

        An illegal character is one that is not typically valid for filesystem
        usage, such as non ascii characters, or can be awkward to use in a
        filesystem, such as spaces. Replace these characters with
        the character specified by *illegal_character_substitute* on
        initialisation. If no character was specified as substitute then return
        *value* unmodified.

        '''
        if self.illegal_character_substitute is None:
            return value

        value = unicodedata.normalize('NFKD', str(value)).encode('ascii', 'ignore')
        value = re.sub('[^\w\.-]', self.illegal_character_substitute, value.decode('utf-8'))
        return str(value.strip().lower())

    def _resolve_project(self, project, context=None):
        return [self.sanitise_for_filesystem(project['name'])]

    def _resolve_context(self, entity, context=None):
        '''Return resource identifier parts from general *entity*.'''

        error_message = (
            'Entity {0!r} must be committed and have a parent context.'.format(
                entity
            )
        )

        link = entity['link']

        if not link:
            raise ftrack_api.exception.StructureError(error_message)

        structure_names = [
            item['name']
            for item in link[1:]
        ]

        parts = self._resolve_project(entity['project'])

        if structure_names:
            for part in structure_names:
                parts.append(self.sanitise_for_filesystem(part))
        elif self.project_versions_prefix:
            # Add *project_versions_prefix* if configured and the version is
            # published directly under the project.
            parts.append(self.sanitise_for_filesystem(self.project_versions_prefix))

        return parts

    def _resolve_asset(self, asset, context=None):
        '''Build asset resource identifier from parent context and asset name.'''
        parts = self._resolve_context(asset['parent'], context=context)
        parts.append(self.sanitise_for_filesystem(asset['name']))
        return parts

    def _format_version(self, number):
        '''Return a formatted string representing version *number*.'''
        return 'v{0:03d}'.format(number)

    def _resolve_version(self, version, version_id=None, context=None):
        '''Get resource identifier for a version.'''

        session = version.session

        if version is ftrack_api.symbol.NOT_SET and version_id:
            version = session.get('AssetVersion', version_id)

        error_message = (
            'Version {0!r} must be committed and have a asset with parent context.'.format(
                version
            )
        )

        if (
            version is ftrack_api.symbol.NOT_SET or
            version in session.created
        ):
            raise ftrack_api.exception.StructureError(error_message)

        # Create version resource identifier from asset and version number
        parts = self._resolve_asset(version['asset'], context=context)
        parts.append(self.sanitise_for_filesystem(version_number))

        return parts

    def _resolve_sequencecomponent(self, sequencecomponent, context=None):
        '''Get resource identifier for a sequence component.'''

        # Create sequence expression for the sequence component and add it
        # to the parts.
        parts = self._resolve_version(sequencecomponent['version'], version_id=sequencecomponent['version_id'], context=context)
        sequence_expression = self._get_sequence_expression(sequencecomponent)
        parts.append(
            '{0}.{1}{2}'.format(
                self.sanitise_for_filesystem(sequencecomponent['name']),
                sequence_expression,
                self.sanitise_for_filesystem(sequencecomponent['file_type'])
            )
        )
        return parts

    def _resolve_container(self, component, container, context=None):
        '''Get resource identifier for a container.'''
        container_path = self.get_resource_identifier(container, context=context)
        if container.entity_type in ('SequenceComponent',):
            # Strip the sequence component expression from the parent
            # container and back the correct filename, i.e.
            # /sequence/component/sequence_component_name.0012.exr.
            name = '{0}.{1}{2}'.format(
                container['name'], component['name'], component['file_type']
            )
            parts = [
                os.path.dirname(container_path),
                self.sanitise_for_filesystem(name)
            ]

        else:
            # Container is not a sequence component so add it as a
            # normal component inside the container.
            name = component['name'] + component['file_type']
            parts = [
                container_path, self.sanitise_for_filesystem(name)
            ]
        return parts

    def _resolve_filecomponent(self, filecomponent, context=None):
        '''Get resource identifier for file component.'''
        container = filecomponent['container']
        if container:
            parts = self._resolve_container(filecomponent, container, context=context)
        else:
            # File component does not have a container, construct name from
            # component name and file type.
            parts = self._resolve_version(filecomponent['version'], version_id=filecomponent['version_id'], context=context)
            name = filecomponent['name'] + filecomponent['file_type']
            parts.append(self.sanitise_for_filesystem(name))
        return parts

    def _resolve_containercomponent(self, containercomponent, context=None):
        # Get resource identifier for container component
        # Add the name of the container to the resource identifier parts.
        parts = self._resolve_version(containercomponent['version'], version_id=containercomponent['version_id'], context=context)
        parts.append(self.sanitise_for_filesystem(containercomponent['name']))
        return parts


    def get_resource_identifier(self, entity, context=None):
        return self.get_resource_identifiers([entity], context=context)[0]

    def get_resource_identifiers(self, entities, context=None):
        '''Return a resource identifier for supplied *entity*.

        *context* can be a mapping that supplies additional information, but
        is unused in this implementation.


        Raise a :py:exc:`ftrack_api.exeption.StructureError` if *entity* is not
        attached to a committed version and a committed asset with a parent
        context.

        '''

        result = []

        self.resolvers = {
            'FileComponent':self._resolve_filecomponent,
            'SequenceComponent': self._resolve_sequencecomponent,
            'ContainerComponent': self._resolve_containercomponent,
            'AssetVersion': self._resolve_version,
            'Asset': self._resolve_asset,
            'Project': self._resolve_project,
            'Context': self._resolve_context,
        }
        for entity in entities:

            if entity.entity_type in self.resolvers:
                parts = self.resolvers[entity.entity_type](entity, context=context)
            else:
                parts = self.resolvers['Context'](entity, context=context)

            result.append(self.path_separator.join(parts))

        return result
