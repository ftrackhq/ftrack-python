# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import collections

import ftrack_api.entity.base
import ftrack_api.exception
import ftrack_api.event.base
import ftrack_api.symbol
import ftrack_api.inspection


class Location(ftrack_api.entity.base.Entity):
    '''Represent storage for components.'''

    def __init__(self, session, data=None, reconstructing=False):
        '''Initialise entity.

        *session* is an instance of :class:`ftrack_api.session.Session` that
        this entity instance is bound to.

        *data* is a mapping of key, value pairs to apply as initial attribute
        values.

        *reconstructing* indicates whether this entity is being reconstructed,
        such as from a query, and therefore should not have any special creation
        logic applied, such as initialising defaults for missing data.

        '''
        self.accessor = ftrack_api.symbol.NOT_SET
        self.structure = ftrack_api.symbol.NOT_SET
        self.resource_identifier_transformer = ftrack_api.symbol.NOT_SET
        self.priority = 95
        super(Location, self).__init__(
            session, data=data, reconstructing=reconstructing
        )

    def __str__(self):
        '''Return string representation of instance.'''
        representation = super(Location, self).__str__()

        with self.session.auto_populating(False):
            name = self['name']
            if name is not ftrack_api.symbol.NOT_SET:
                representation = representation.replace(
                    '(', '("{0}", '.format(name)
                )

        return representation

    def add_component(self, component, source, recursive=True):
        '''Add *component* to location.

        *component* should be a single component instance.

        *source* should be an instance of another location that acts as the
        source.

        Raise :exc:`ftrack_api.ComponentInLocationError` if the *component*
        already exists in this location.

        Raise :exc:`ftrack_api.LocationError` if managing data and the generated
        target structure for the component already exists according to the
        accessor. This helps prevent potential data loss by avoiding overwriting
        existing data. Note that there is a race condition between the check and
        the write so if another process creates data at the same target during
        that period it will be overwritten.

        '''
        return self.add_components(
            [component], sources=source, recursive=recursive
        )

    def add_components(self, components, sources, recursive=True):
        '''Add *components* to location.

        *components* should be a list of component instances.

        *sources* may be either a single source or a list of sources. If a list
        *then each corresponding index in *sources* will be used for each
        *component*. A source should be an instance of another location.

        Raise :exc:`ftrack_api.ComponentInLocationError` if the *component*
        already exists in this location.

        Raise :exc:`ftrack_api.LocationError` if managing data and the generated
        target structure for the component already exists according to the
        accessor. This helps prevent potential data loss by avoiding overwriting
        existing data. Note that there is a race condition between the check and
        the write so if another process creates data at the same target during
        that period it will be overwritten.

        '''
        if (
            isinstance(sources, basestring)
            or not isinstance(sources, collections.Sequence)
        ):
            sources = [sources]

        sources_count = len(sources)
        if sources_count not in (1, len(components)):
            raise ValueError(
                'sources must be either a single source or a sequence of '
                'sources with indexes corresponding to passed components.'
            )

        if not self.structure:
            raise ftrack_api.exception.LocationError(
                'No structure defined for location {location}.',
                details=dict(location=self)
            )

        # Add each component.
        for index, component in enumerate(components):
            # Preemptively check that component has not already been added.
            try:
                self.get_resource_identifier(component)
            except ftrack_api.exception.ComponentNotInLocationError:
                # Component does not already exist in location so it is fine to
                # continue to add it.
                pass
            else:
                raise ftrack_api.exception.ComponentInLocationError(
                    component, self
                )

            # Determine appropriate source.
            if sources_count == 1:
                source = sources[0]
            else:
                source = sources[index]

            # Add members first for container components.
            is_container = 'members' in component.keys()
            if is_container and recursive:
                self.add_components(
                    component['members'], source, recursive=recursive
                )

            # Add component to this location.
            context = self._get_context(component, source)
            resource_identifier = self.structure.get_resource_identifier(
                component, context
            )

            # Manage data transfer.
            self._add_data(component, resource_identifier, source)

            # Optionally encode resource identifier before storing.
            if self.resource_identifier_transformer:
                resource_identifier = (
                    self.resource_identifier_transformer.encode(
                        resource_identifier,
                        context={'component': component}
                    )
                )

            # Store component in location information.
            self._register_component_in_location(component, resource_identifier)

            # Publish event.
            component_id = ftrack_api.inspection.primary_key(
                component
            ).values()[0]
            location_id = ftrack_api.inspection.primary_key(self).values()[0]

            self.session.event_hub.publish(
                ftrack_api.event.base.Event(
                    topic=ftrack_api.symbol.COMPONENT_ADDED_TO_LOCATION_TOPIC,
                    data=dict(
                        component_id=component_id,
                        location_id=location_id
                    ),
                ),
                on_error='ignore'
            )

    def _get_context(self, component, source):
        '''Return context for *component* and *source*.'''
        context = {}
        if source:
            try:
                source_resource_identifier = source.get_resource_identifier(
                    component
                )
            except ftrack_api.exception.ComponentNotInLocationError:
                pass
            else:
                context.update(dict(
                    source_resource_identifier=source_resource_identifier
                ))

        return context

    def _add_data(self, component, resource_identifier, source):
        '''Manage transfer of *component* data from *source*.

        *resource_identifier* specifies the identifier to use with this
        locations accessor.

        '''
        # Read data from source and write to this location.
        if not source.accessor:
            raise ftrack_api.exception.LocationError(
                'No accessor defined for source location {location}.',
                details=dict(location=source)
            )

        if not self.accessor:
            raise ftrack_api.exception.LocationError(
                'No accessor defined for target location {location}.',
                details=dict(location=self)
            )

        is_container = 'members' in component.keys()
        if is_container:
            # TODO: Improve this check. Possibly introduce an inspection
            # such as ftrack_api.inspection.is_sequence_component.
            if component.entity_type != 'SequenceComponent':
                self.accessor.make_container(resource_identifier)

        else:
            # Try to make container of component.
            try:
                container = self.accessor.get_container(
                    resource_identifier
                )

            except ftrack_api.exception.AccessorParentResourceNotFoundError:
                # Container could not be retrieved from
                # resource_identifier. Assume that there is no need to
                # make the container.
                pass

            else:
                # No need for existence check as make_container does not
                # recreate existing containers.
                self.accessor.make_container(container)

            if self.accessor.exists(resource_identifier):
                # Note: There is a race condition here in that the
                # data may be added externally between the check for
                # existence and the actual write which would still
                # result in potential data loss. However, there is no
                # good cross platform, cross accessor solution for this
                # at present.
                raise ftrack_api.exception.LocationError(
                    'Cannot add component as data already exists and '
                    'overwriting could result in data loss. Computed '
                    'target resource identifier was: {0}'
                    .format(resource_identifier)
                )

            # Read and write data.
            source_data = source.accessor.open(
                source.get_resource_identifier(component), 'rb'
            )
            target_data = self.accessor.open(resource_identifier, 'wb')
            target_data.write(source_data.read())
            target_data.close()
            source_data.close()

    def _register_component_in_location(self, component, resource_identifier):
        '''Register *component* in location with *resource_identifier*.'''
        self.session.create(
            'ComponentLocation', data=dict(
                component=component,
                location=self,
                resource_identifier=resource_identifier
            )
        )

        # TODO: Should auto-commit here be optional?
        self.session.commit()

    def remove_component(self, component, recursive=True):
        '''Remove *component* from location.'''
        return self.remove_components([component], recursive=recursive)

    def remove_components(self, components, recursive=True):
        '''Remove *components* from location.'''
        for component in components:
            # Check component is in this location
            self.get_resource_identifier(component)

            # Remove members first for container components.
            is_container = 'members' in component.keys()
            if is_container and recursive:
                self.remove_components(
                    component['members'], recursive=recursive
                )

            # Remove data.
            self._remove_data(component)

            # Remove metadata.
            self._deregister_component_in_location(component)

            # Emit event.
            component_id = ftrack_api.inspection.primary_key(
                component
            ).values()[0]
            location_id = ftrack_api.inspection.primary_key(self).values()[0]
            self.session.event_hub.publish(
                ftrack_api.event.base.Event(
                    topic=ftrack_api.symbol.COMPONENT_REMOVED_FROM_LOCATION_TOPIC,
                    data=dict(
                        component_id=component_id,
                        location_id=location_id
                    )
                ),
                on_error='ignore'
            )

    def _remove_data(self, component):
        '''Remove data associated with *component*.'''
        if not self.accessor:
            raise ftrack_api.exception.LocationError(
                'No accessor defined for location {location}.',
                details=dict(location=self)
            )

        try:
            self.accessor.remove(
                self.get_resource_identifier(component)
            )
        except ftrack_api.exception.AccessorResourceNotFoundError:
            # If accessor does not support detecting sequence paths then an
            # AccessorResourceNotFoundError is raised. For now, if the
            # component type is 'SequenceComponent' assume success.
            if not component.entity_type == 'SequenceComponent':
                raise

    def _deregister_component_in_location(self, component):
        '''Deregister *component* from location.'''
        component_id = ftrack_api.inspection.primary_key(component).values()[0]
        location_id = ftrack_api.inspection.primary_key(self).values()[0]

        # TODO: Use session.get for optimisation.
        component_location = self.session.query(
            'ComponentLocation where component_id is {0} and location_id is '
            '{1}'.format(component_id, location_id)
        )[0]

        self.session.delete(component_location)

        # TODO: Should auto-commit here be optional?
        self.session.commit()

    def get_component_availability(self, component):
        '''Return availability of *component* in this location as a float.'''
        return self.session.get_component_availability(
            component, locations=[self]
        )[self['id']]

    def get_component_availabilities(self, components):
        '''Return availabilities of *components* in this location.

        Return list of float values corresponding to each component.

        '''
        return [
            availability[self['id']] for availability in
            self.session.get_component_availabilities(
                components, locations=[self]
            )
        ]

    def get_resource_identifier(self, component):
        '''Return resource identifier for *component*.

        Raise :exc:`ftrack_api.exception.ComponentNotInLocationError` if the
        component is not present in this location.

        '''
        return self.get_resource_identifiers([component])[0]

    def get_resource_identifiers(self, components):
        '''Return resource identifiers for *components*.

        Raise :exc:`ftrack_api.exception.ComponentNotInLocationError` if any
        of the components are not present in this location.

        '''
        resource_identifiers = self._get_resource_identifiers(components)

        # Optionally decode resource identifier.
        if self.resource_identifier_transformer:
            for index, resource_identifier in enumerate(resource_identifiers):
                resource_identifiers[index] = (
                    self.resource_identifier_transformer.decode(
                        resource_identifier
                    )
                )

        return resource_identifiers

    def _get_resource_identifiers(self, components):
        '''Return resource identifiers for *components*.

        Raise :exc:`ftrack_api.exception.ComponentNotInLocationError` if any
        of the components are not present in this location.

        '''
        component_ids_mapping = collections.OrderedDict()
        for component in components:
            component_id = ftrack_api.inspection.primary_key(
                component
            ).values()[0]
            component_ids_mapping[component_id] = component

        component_locations = self.session.query(
            'select component_id, resource_identifier from ComponentLocation '
            'where location_id is {0} and component_id in ({1})'
            .format(
                ftrack_api.inspection.primary_key(self).values()[0],
                ', '.join(component_ids_mapping.keys())
            )
        )

        resource_identifiers_map = {}
        for component_location in component_locations:
            resource_identifiers_map[component_location['component_id']] = (
                component_location['resource_identifier']
            )

        resource_identifiers = []
        missing = []
        for component_id, component in component_ids_mapping.items():
            if component_id not in resource_identifiers_map:
                missing.append(component)
            else:
                resource_identifiers.append(
                    resource_identifiers_map[component_id]
                )

        if missing:
            raise ftrack_api.exception.ComponentNotInLocationError(
                missing, self
            )

        return resource_identifiers

    def get_filesystem_path(self, component):
        '''Return filesystem path for *component*.'''
        return self.get_filesystem_paths([component])[0]

    def get_filesystem_paths(self, components):
        '''Return filesystem paths for *components*.'''
        resource_identifiers = self.get_resource_identifiers(components)

        filesystem_paths = []
        for resource_identifier in resource_identifiers:
            filesystem_paths.append(
                self.accessor.get_filesystem_path(resource_identifier)
            )

        return filesystem_paths


class MemoryLocationMixin(object):
    '''Represent storage for components.

    Unlike a standard location, only store metadata for components in this
    location in memory rather than persisting to the database.

    '''

    @property
    def _cache(self):
        '''Return cache.'''
        try:
            cache = self.__cache
        except AttributeError:
            cache = self.__cache = {}

        return cache

    def _register_component_in_location(self, component, resource_identifier):
        '''Register *component* in location with *resource_identifier*.'''
        component_id = ftrack_api.inspection.primary_key(component).values()[0]
        self._cache[component_id] = resource_identifier

    def _deregister_component_in_location(self, component):
        '''Deregister *component* in location.'''
        component_id = ftrack_api.inspection.primary_key(component).values()[0]
        self._cache.pop(component_id)

    def _get_resource_identifiers(self, components):
        '''Return resource identifiers for *components*.

        Raise :exc:`ftrack_api.exception.ComponentNotInLocationError` if any
        of the referenced components are not present in this location.

        '''
        resource_identifiers = []
        missing = []
        for component in components:
            component_id = ftrack_api.inspection.primary_key(
                component
            ).values()[0]
            resource_identifier = self._cache.get(component_id)
            if resource_identifier is None:
                missing.append(component)
            else:
                resource_identifiers.append(resource_identifier)

        if missing:
            raise ftrack_api.exception.ComponentNotInLocationError(
                missing, self
            )

        return resource_identifiers


class UnmanagedLocationMixin(object):
    '''Location that does not manage data.'''

    def _add_data(self, component, resource_identifier, source):
        '''Manage transfer of *component* data from *source*.

        *resource_identifier* specifies the identifier to use with this
        locations accessor.

        Overridden to have no effect.

        '''
        return

    def _remove_data(self, component):
        '''Remove data associated with *component*.

        Overridden to have no effect.

        '''
        return


class OriginLocationMixin(MemoryLocationMixin, UnmanagedLocationMixin):
    '''Special origin location that expects sources as filepaths.'''

    def _get_context(self, component, source):
        '''Return context for *component* and *source*.'''
        context = {}
        if source:
            context.update(dict(
                source_resource_identifier=source
            ))

        return context
