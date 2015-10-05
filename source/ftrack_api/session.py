# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import json
import logging
import collections
import datetime
import os
import getpass
import functools
import itertools
import distutils.version

import requests
import requests.auth
import arrow
import clique

import ftrack_api
import ftrack_api.exception
import ftrack_api.entity.factory
import ftrack_api.entity.base
import ftrack_api.entity.location
import ftrack_api.cache
import ftrack_api.symbol
import ftrack_api.query
import ftrack_api.attribute
import ftrack_api.collection
import ftrack_api.event.hub
import ftrack_api.event.base
import ftrack_api.plugin
import ftrack_api.inspection
import ftrack_api.operation
import ftrack_api.accessor.disk
import ftrack_api.structure.origin
import ftrack_api.structure.entity_id
import ftrack_api.accessor.server


class SessionAuthentication(requests.auth.AuthBase):
    '''Attach ftrack session authentication information to requests.'''

    def __init__(self, api_key, api_user):
        '''Initialise with *api_key* and *api_user*.'''
        self.api_key = api_key
        self.api_user = api_user
        super(SessionAuthentication, self).__init__()

    def __call__(self, request):
        '''Modify *request* to have appropriate headers.'''
        request.headers.update({
            'ftrack-api-key': self.api_key,
            'ftrack-user': self.api_user
        })
        return request


class Session(object):
    '''An isolated session for interaction with an ftrack server.'''

    def __init__(
        self, server_url=None, api_key=None, api_user=None, auto_populate=True,
        plugin_paths=None, cache=None, cache_key_maker=None,
        auto_connect_event_hub=True
    ):
        '''Initialise session.

        *server_url* should be the URL of the ftrack server to connect to
        including any port number. If not specified attempt to look up from
        :envvar:`FTRACK_SERVER`.

        *api_key* should be the API key to use for authentication whilst
        *api_user* should be the username of the user in ftrack to record
        operations against. If not specified, *api_key* should be retrieved
        from :envvar:`FTRACK_API_KEY` and *api_user* from
        :envvar:`FTRACK_API_USER`.

        If *auto_populate* is True (the default), then accessing entity
        attributes will cause them to be automatically fetched from the server
        if they are not already. This flag can be changed on the session
        directly at any time.

        *plugin_paths* should be a list of paths to search for plugins. If not
        specified, default to looking up :envvar:`FTRACK_EVENT_PLUGIN_PATH`.

        *cache* should be an instance of a cache that fulfils the
        :class:`ftrack_api.cache.Cache` interface and will be used as the cache
        for the session. It can also be a callable that will be called with the
        session instance as sole argument.

        .. note::

            The session will add the specified cache to a pre-configured layered
            cache that specifies the top level cache as a
            :class:`ftrack_api.cache.MemoryCache`. Therefore, it is unnecessary 
            to construct a separate memory cache for typical behaviour. Working
            around this behaviour or removing the memory cache can lead to
            unexpected behaviour.

        *cache_key_maker* should be an instance of a key maker that fulfils the
        :class:`ftrack_api.cache.KeyMaker` interface and will be used to 
        generate keys for objects being stored in the *cache*. If not specified, 
        a :class:`~ftrack_api.cache.StringKeyMaker` will be used.

        If *auto_connect_event_hub* is True then embedded event hub will be
        automatically connected to the event server and allow for publishing and
        subscribing to **non-local** events. If False, then only publishing and
        subscribing to **local** events will be possible until the hub is
        manually connected using :meth:`EventHub.connect
        <ftrack_api.event.hub.EventHub.connect>`.

        '''
        super(Session, self).__init__()
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        if server_url is None:
            server_url = os.environ.get('FTRACK_SERVER')

        if not server_url:
            raise TypeError(
                'Required "server_url" not specified. Pass as argument or set '
                'in environment variable FTRACK_SERVER.'
            )

        self._server_url = server_url

        if api_key is None:
            api_key = os.environ.get(
                'FTRACK_API_KEY',
                # Backwards compatibility
                os.environ.get('FTRACK_APIKEY')
            )

        if not api_key:
            raise TypeError(
                'Required "api_key" not specified. Pass as argument or set in '
                'environment variable FTRACK_API_KEY.'
            )

        self._api_key = api_key

        if api_user is None:
            api_user = os.environ.get('FTRACK_API_USER')
            if not api_user:
                try:
                    api_user = getpass.getuser()
                except Exception:
                    pass

        if not api_user:
            raise TypeError(
                'Required "api_user" not specified. Pass as argument, set in '
                'environment variable FTRACK_API_USER or one of the standard '
                'environment variables used by Python\'s getpass module.'
            )

        self._api_user = api_user

        # Currently pending operations.
        self.recorded_operations = ftrack_api.operation.Operations()
        self.record_operations = True

        self.cache_key_maker = cache_key_maker
        if self.cache_key_maker is None:
            self.cache_key_maker = ftrack_api.cache.StringKeyMaker()

        # Enforce always having a memory cache at top level so that the same
        # in-memory instance is returned from session.
        self.cache = ftrack_api.cache.LayeredCache([
            ftrack_api.cache.MemoryCache()
        ])

        if cache is not None:
            if callable(cache):
                cache = cache(self)

            self.cache.caches.append(cache)

        self._attached = collections.OrderedDict()

        self._request = requests.Session()
        self._request.auth = SessionAuthentication(
            self._api_key, self._api_user
        )

        self.auto_populate = auto_populate

        # Fetch server information and in doing so also check credentials.
        self._server_information = self._fetch_server_information()

        # Now check compatibility of server based on retrieved information.
        self.check_server_compatibility()

        # Construct event hub and load plugins.
        self._event_hub = ftrack_api.event.hub.EventHub(
            self._server_url,
            self._api_user,
            self._api_key
        )

        if auto_connect_event_hub:
            self._event_hub.connect()

        self._plugin_paths = plugin_paths
        if self._plugin_paths is None:
            self._plugin_paths = os.environ.get(
                'FTRACK_EVENT_PLUGIN_PATH', ''
            ).split(os.pathsep)

        self._discover_plugins()

        # TODO: Make schemas read-only and non-mutable (or at least without
        # rebuilding types)?
        self.schemas = self._fetch_schemas()
        self.types = self._build_entity_type_classes(self.schemas)

        self._configure_locations()

    @property
    def server_information(self):
        '''Return server information such as server version.'''
        return self._server_information.copy()

    @property
    def server_url(self):
        '''Return server ulr used for session.'''
        return self._server_url

    @property
    def api_user(self):
        '''Return username used for session.'''
        return self._api_user

    @property
    def api_key(self):
        '''Return API key used for session.'''
        return self._api_key

    @property
    def event_hub(self):
        '''Return event hub.'''
        return self._event_hub

    def check_server_compatibility(self):
        '''Check compatibility with connected server.'''
        server_version = self.server_information.get('version')
        if server_version is None:
            raise ftrack_api.exception.ServerCompatibilityError(
                'Could not determine server version.'
            )

        # Perform basic version check.
        if server_version != 'dev':
            server_version_range = ('3.2.1', '3.4')
            if not (
                distutils.version.LooseVersion(server_version_range[0])
                <= distutils.version.LooseVersion(server_version)
                < distutils.version.LooseVersion(server_version_range[1])
            ):
                raise ftrack_api.exception.ServerCompatibilityError(
                    'Server version {0} incompatible with this version of the '
                    'API which requires a server version >= {1}, < {2}'.format(
                        server_version,
                        server_version_range[0],
                        server_version_range[1]
                    )
                )

    def reset(self):
        '''Reset session clearing all locally stored data.

        If the cache used by the session is a
        :class:`~ftrack_api.cache.LayeredCache` then only clear top level cache.
        Otherwise, clear the entire cache.

        '''
        if self.recorded_operations:
            self.logger.warning(
                'Resetting session with pending operations not persisted.'
            )

        if isinstance(self.cache, ftrack_api.cache.LayeredCache):
            try:
                self.cache.caches[0].clear()
            except IndexError:
                pass
        elif isinstance(self.cache, ftrack_api.cache.Cache):
            self.cache.clear()

        self._attached.clear()
        self.recorded_operations.clear()
        self._request.close()

    def auto_populating(self, auto_populate):
        '''Temporarily set auto populate to *auto_populate*.

        The current setting will be restored automatically when done.

        Example::

            with session.auto_populating(False):
                print entity['name']

        '''
        return AutoPopulatingContext(self, auto_populate)

    def operation_recording(self, record_operations):
        '''Temporarily set operation recording to *record_operations*.

        The current setting will be restored automatically when done.

        Example::

            with session.operation_recording(False):
                entity['name'] = 'change_not_recorded'

        '''
        return OperationRecordingContext(self, record_operations)

    @property
    def created(self):
        '''Return list of newly created entities.'''
        entities = self._attached.values()
        states = ftrack_api.inspection.states(entities)

        return [
            entity for (entity, state) in itertools.izip(entities, states)
            if state is ftrack_api.symbol.CREATED
        ]

    @property
    def modified(self):
        '''Return list of locally modified entities.'''
        entities = self._attached.values()
        states = ftrack_api.inspection.states(entities)

        return [
            entity for (entity, state) in itertools.izip(entities, states)
            if state is ftrack_api.symbol.MODIFIED
        ]

    @property
    def deleted(self):
        '''Return list of deleted entities.'''
        entities = self._attached.values()
        states = ftrack_api.inspection.states(entities)

        return [
            entity for (entity, state) in itertools.izip(entities, states)
            if state is ftrack_api.symbol.DELETED
        ]

    def create(self, entity_type, data=None, reconstructing=False):
        '''Create and return an entity of *entity_type* with initial *data*.

        If specified, *data* should be a dictionary of key, value pairs that
        should be used to populate attributes on the entity.

        If *reconstructing* is False then create a new entity setting
        appropriate defaults for missing data. If True then reconstruct an
        existing entity.

        Constructed entity will be automatically :meth:`merged <Session.merge>`
        into the session.

        '''
        entity = self._create(entity_type, data, reconstructing=reconstructing)
        entity = self.merge(entity)

        if not reconstructing:

            # Record create operation.
            # This is done here rather than in the Entity constructor in order
            # to ensure that all recorded values are fully merged into session.
            if self.record_operations:
                entity_data = {}

                # Lower level API used here to avoid including any empty
                # collections that are automatically generated on access.
                for attribute in entity.attributes:
                    value = attribute.get_local_value(entity)
                    if value is not ftrack_api.symbol.NOT_SET:
                        entity_data[attribute.name] = value

                self.recorded_operations.push(
                    ftrack_api.operation.CreateEntityOperation(
                        entity.entity_type,
                        ftrack_api.inspection.primary_key(entity),
                        entity_data
                    )
                )

        return entity

    def _create(self, entity_type, data, reconstructing):
        '''Create and return an entity of *entity_type* with initial *data*.'''
        try:
            EntityTypeClass = self.types[entity_type]
        except KeyError:
            raise ftrack_api.exception.UnrecognisedEntityTypeError(entity_type)

        return EntityTypeClass(self, data=data, reconstructing=reconstructing)

    def ensure(self, entity_type, data, identifying_keys=None):
        '''Retrieve entity of *entity_type* with *data*, creating if necessary.

        *data* should be a dictionary of the same form passed to :meth:`create`.

        By default, check for an entity that has matching *data*. If
        *identifying_keys* is specified as a list of keys then only consider the
        values from *data* for those keys when searching for existing entity. If
        *data* is missing an identifying key then raise :exc:`KeyError`.

        If no *identifying_keys* specified then use all of the keys from the
        passed *data*. Raise :exc:`ValueError` if no *identifying_keys* can be
        determined.

        Each key should be a string.

        .. note::

            Currently only top level scalars supported. To ensure an entity by
            looking at relationships, manually issue the :meth:`query` and
            :meth:`create` calls.

        If more than one entity matches the determined filter criteria then
        raise :exc:`~ftrack_api.exception.MultipleResultsFoundError`.

        If no matching entity found then create entity using supplied *data*.

        If a matching entity is found, then update it if necessary with *data*.

        .. note::

            If entity created or updated then a :meth:`commit` will be issued
            automatically. If this behaviour is undesired, perform the
            :meth:`query` and :meth:`create` calls manually.

        Return retrieved or created entity.

        Example::

            # First time, a new entity with `username=martin` is created.
            entity = session.ensure('User', {'username': 'martin'})

            # After that, the existing entity is retrieved.
            entity = session.ensure('User', {'username': 'martin'})

            # When existing entity retrieved, entity may also be updated to
            # match supplied data.
            entity = session.ensure(
                'User', {'username': 'martin', 'email': 'martin@example.com'}
            )

        '''
        if not identifying_keys:
            identifying_keys = data.keys()

        self.logger.debug(
            'Ensuring entity {0!r} with data {1!r} using identifying keys {2!r}'
            .format(entity_type, data, identifying_keys)
        )

        if not identifying_keys:
            raise ValueError(
                'Could not determine any identifying data to check against '
                'when ensuring {0!r} with data {1!r}. Identifying keys: {2!r}'
                .format(entity_type, data, identifying_keys)
            )

        expression = '{0} where'.format(entity_type)
        criteria = []
        for identifying_key in identifying_keys:
            value = data[identifying_key]

            if isinstance(value, basestring):
                value = '"{0}"'.format(value)

            elif isinstance(
                value, (arrow.Arrow, datetime.datetime, datetime.date)
            ):
                # Server does not store microsecond or timezone currently so
                # need to strip from query.
                # TODO: When datetime handling improved, update this logic.
                value = (
                    arrow.get(value).naive.replace(microsecond=0).isoformat()
                )
                value = '"{0}"'.format(value)

            criteria.append('{0} is {1}'.format(identifying_key, value))

        expression = '{0} {1}'.format(
            expression, ' and '.join(criteria)
        )

        try:
            entity = self.query(expression).one()

        except ftrack_api.exception.NoResultFoundError:
            self.logger.debug('Creating entity as did not already exist.')

            # Create entity.
            entity = self.create(entity_type, data)
            self.commit()

        else:
            self.logger.debug('Retrieved matching existing entity.')

            # Update entity if required.
            updated = False
            for key, target_value in data.items():
                if entity[key] != target_value:
                    entity[key] = target_value
                    updated = True

            if updated:
                self.logger.debug('Updating existing entity to match new data.')
                self.commit()

        return entity

    def delete(self, entity):
        '''Mark *entity* for deletion.'''
        if self.record_operations:
            self.recorded_operations.push(
                ftrack_api.operation.DeleteEntityOperation(
                    entity.entity_type,
                    ftrack_api.inspection.primary_key(entity)
                )
            )

    def get(self, entity_type, entity_key):
        '''Return entity of *entity_type* with unique *entity_key*.

        First check for an existing entry in the configured cache, otherwise
        issue a query to the server.

        If no matching entity found, return None.

        '''
        self.logger.debug(
            'Get {0} with key {1}'.format(entity_type, entity_key)
        )

        primary_key_definition = self.types[entity_type].primary_key_attributes
        if isinstance(entity_key, basestring):
            entity_key = [entity_key]

        if len(entity_key) != len(primary_key_definition):
            raise ValueError(
                'Incompatible entity_key {0!r} supplied. Entity type {1} '
                'expects a primary key composed of {2} values ({3}).'
                .format(
                    entity_key, entity_type, len(primary_key_definition),
                    ', '.join(primary_key_definition)
                )
            )

        entity = None
        try:
            entity = self._get(entity_type, entity_key)

            # Ensure any references in the retrieved cache object are expanded.
            self._merge_references(entity)

        except KeyError:

            # Query for matching entity.
            self.logger.debug(
                'Entity not present in cache. Issuing new query.'
            )
            condition = []
            for key, value in zip(primary_key_definition, entity_key):
                condition.append('{0} is "{1}"'.format(key, value))

            expression = '{0} where ({1})'.format(
                entity_type, ' and '.join(condition)
            )

            results = self.query(expression).all()
            if results:
                entity = results[0]

        return entity

    def _get(self, entity_type, entity_key):
        '''Return cached entity of *entity_type* with unique *entity_key*.

        Raise :exc:`KeyError` if no such entity in the cache.

        '''
        # Check cache for existing entity emulating
        # ftrack_api.inspection.identity result object to pass to key maker.
        cache_key = self.cache_key_maker.key(
            (str(entity_type), map(str, entity_key))
        )
        self.logger.debug(
            'Checking cache for entity with key {0}'.format(cache_key)
        )
        entity = self.cache.get(cache_key)
        self.logger.debug(
            'Retrieved existing entity from cache: {0} at {1}'
            .format(entity, id(entity))
        )

        return entity

    def query(self, expression):
        '''Query against remote data according to *expression*.

        *expression* is not executed directly. Instead return an
        :class:`ftrack_api.query.QueryResult` instance that will execute remote
        call on access.

        .. seealso:: :ref:`querying`

        '''
        self.logger.debug(
            'Query {0!r}'.format(expression)
        )

        # Add in sensible projections if none specified. Note that this is
        # done here rather than on the server to allow local modification of the
        # schema setting to include commonly used custom attributes for example.
        # TODO: Use a proper parser perhaps?
        if not expression.startswith('select'):
            entity_type = expression.split(' ', 1)[0]
            EntityTypeClass = self.types[entity_type]
            projections = EntityTypeClass.default_projections

            expression = 'select {0} from {1}'.format(
                ', '.join(projections),
                expression
            )

        query_result = ftrack_api.query.QueryResult(self, expression)
        return query_result

    def _query(self, expression):
        '''Execute *query*.'''
        # TODO: Actually support batching several queries together.
        # TODO: Should batches have unique ids to match them up later.
        batch = [{
            'action': 'query',
            'expression': expression
        }]

        # TODO: When should this execute? How to handle background=True?
        results = self._call(batch)

        # Merge entities into local cache and return merged entities.
        data = []
        for entity in results[0]['data']:
            data.append(self.merge(entity))

        return data

    def _attach(self, entity):
        '''Attach *entity* to session if not already.'''
        key = str(ftrack_api.inspection.identity(entity))
        current = self._attached.get(key)

        if current is None:
            self._attached[key] = entity

        elif current is not entity:
            raise ValueError(
                'Cannot attach {0!r}. A different instance {1!r} of that '
                'entity is already attached.'.format(entity, current)
            )

    def _detach(self, entity):
        '''Detach *entity* from session.'''
        key = str(ftrack_api.inspection.identity(entity))
        del self._attached[key]

    def merge(self, value, merged=None):
        '''Merge *value* into session and return merged value.

        *merged* should be a mapping to record merges during run and should be
        used to avoid infinite recursion. If not set will default to a
        dictionary.

        '''
        if merged is None:
            merged = {}

        with self.operation_recording(False):
            return self._merge(value, merged)

    def _merge(self, value, merged):
        '''Return merged *value*.'''
        if isinstance(value, ftrack_api.entity.base.Entity):
            self.logger.debug(
                'Merging entity into session: {0} at {1}'
                .format(value, id(value))
            )
            return self._merge_entity(value, merged=merged)

        elif isinstance(value, ftrack_api.collection.Collection):
            self.logger.debug(
                'Merging collection into session: {0!r} at {1}'
                .format(value, id(value))
            )

            merged_collection = []
            for entry in value:
                merged_collection.append(
                    self._merge(entry, merged=merged)
                )

            return merged_collection

        elif isinstance(value, ftrack_api.collection.MappedCollectionProxy):
            self.logger.debug(
                'Merging mapped collection into session: {0!r} at {1}'
                .format(value, id(value))
            )

            merged_collection = []
            for entry in value.collection:
                merged_collection.append(
                    self._merge(entry, merged=merged)
                )

            return merged_collection

        else:
            return value

    def _merge_entity(self, entity, merged=None):
        '''Merge *entity* into session returning merged entity.

        Merge is recursive so any references to other entities will also be
        merged.

        *entity* will never be modified in place. Ensure that the returned
        merged entity instance is used.

        '''
        if merged is None:
            merged = {}

        with self.auto_populating(False):
            entity_key = self.cache_key_maker.key(
                ftrack_api.inspection.identity(entity)
            )

            # Check whether this entity has already been processed.
            attached_entity = merged.get(entity_key)
            if attached_entity is not None:
                self.logger.debug(
                    'Entity already processed for key {0} as {1} at {2}'
                    .format(entity_key, attached_entity, id(attached_entity))
                )
                return attached_entity

            # Check for existing instance of entity in cache.
            self.logger.debug(
                'Checking for entity in cache with key {0}'.format(entity_key)
            )

            try:
                attached_entity = self.cache.get(entity_key)
                self.logger.debug(
                    'Retrieved existing entity from cache: {0} at {1}'
                    .format(attached_entity, id(attached_entity))
                )

            except KeyError:
                # Construct new minimal instance to store in cache.
                attached_entity = self._create(
                    entity.entity_type, {}, reconstructing=True
                )
                self.logger.debug(
                    'Entity not present in cache. Constructed new instance: '
                    '{0} at {1}'.format(attached_entity, id(attached_entity))
                )

            # Mark entity as seen to avoid infinite loops.
            merged[entity_key] = attached_entity

            # Expand references. This is required as a serialised cache might
            # have returned just a plain entity object with the rest of the data
            # stored separately. The reason this is done here rather in the
            # specific cache is so that any higher level cache can be taken
            # advantage of when fetching data.
            self._merge_references(attached_entity, merged=merged)

            # Merge new entity data into cache entity. If this causes the cache
            # entity to change then persist those changes back to the cache.
            self.logger.debug('Merging new data into attached entity.')
            changes = attached_entity.merge(entity, merged=merged)
            if changes:
                self.cache.set(entity_key, attached_entity)
                self.logger.debug('Cache updated with merged entity.')
            else:
                self.logger.debug(
                    'Cache not updated with merged entity as no differences '
                    'detected.'
                )

            # Ensure this instance is now attached to the session.
            self._attach(attached_entity)

        return attached_entity

    def _merge_references(self, entity, merged=None):
        '''Recursively merge entity references in *entity*.'''
        self.logger.debug('Merging references.')

        if merged is None:
            merged = {}

        for attribute in entity.attributes:

            # Local attributes.
            local_value = attribute.get_local_value(entity)
            if isinstance(
                local_value,
                (
                    ftrack_api.entity.base.Entity, 
                    ftrack_api.collection.Collection,
                    ftrack_api.collection.MappedCollectionProxy
                )
            ):
                self.logger.debug(
                    'Merging local value for attribute {0}.'.format(attribute)
                )

                merged_local_value = self._merge(local_value, merged=merged)
                if merged_local_value is not local_value:
                    with self.operation_recording(False):
                        attribute.set_local_value(entity, merged_local_value)

            # Remote attributes.
            remote_value = attribute.get_remote_value(entity)
            if isinstance(
                remote_value,
                (
                    ftrack_api.entity.base.Entity, 
                    ftrack_api.collection.Collection,
                    ftrack_api.collection.MappedCollectionProxy
                )
            ):
                self.logger.debug(
                    'Merging remote value for attribute {0}.'.format(attribute)
                )

                merged_remote_value = self._merge(remote_value, merged=merged)
                if merged_remote_value is not remote_value:
                    attribute.set_remote_value(entity, merged_remote_value)

    def populate(self, entities, projections):
        '''Populate *entities* with attributes specified by *projections*.

        Any locally set values included in the *projections* will not be
        overwritten with the retrieved remote value. If this 'synchronise'
        behaviour is required, first clear the relevant values on the entity by
        setting them to :attr:`ftrack_api.symbol.NOT_SET`. Deleting the key will
        have the same effect::

            >>> print(user['username'])
            martin
            >>> del user['username']
            >>> print(user['username'])
            Symbol(NOT_SET)

        .. note::

            Entities that have been created and not yet persisted will be
            skipped as they have no remote values to fetch.

        '''
        self.logger.debug(
            'Populate {0!r} projections for {1}.'.format(projections, entities)
        )

        if not isinstance(
            entities, (list, tuple, ftrack_api.query.QueryResult)
        ):
            entities = [entities]

        # TODO: How to handle a mixed collection of different entity types
        # Should probably fail, but need to consider handling hierarchies such
        # as User and Group both deriving from Resource. Actually, could just
        # proceed and ignore projections that are not present in entity type.

        entities_to_process = []

        for entity in entities:
            if ftrack_api.inspection.state(entity) is ftrack_api.symbol.CREATED:
                # Created entities that are not yet persisted have no remote
                # values. Don't raise an error here as it is reasonable to
                # iterate over an entities properties and see that some of them
                # are NOT_SET.
                self.logger.debug(
                    'Skipping newly created entity {0!r} for population as no '
                    'data will exist in the remote for this entity yet.'
                    .format(entity)
                )
                continue

            entities_to_process.append(entity)

        if entities_to_process:
            reference_entity = entities_to_process[0]
            entity_type = reference_entity.entity_type
            query = 'select {0} from {1}'.format(projections, entity_type)

            primary_key_definition = reference_entity.primary_key_attributes
            entity_keys = [
                ftrack_api.inspection.primary_key(entity).values()
                for entity in entities_to_process
            ]

            if len(primary_key_definition) > 1:
                # Composite keys require full OR syntax unfortunately.
                conditions = []
                for entity_key in entity_keys:
                    condition = []
                    for key, value in zip(primary_key_definition, entity_key):
                        condition.append('{0} is "{1}"'.format(key, value))

                    conditions.append('({0})'.format('and '.join(condition)))

                query = '{0} where {1}'.format(query, ' or '.join(conditions))

            else:
                primary_key = primary_key_definition[0]

                if len(entity_keys) > 1:
                    query = '{0} where {1} in ({2})'.format(
                        query, primary_key,
                        ','.join([
                            str(entity_key[0]) for entity_key in entity_keys
                        ])
                    )
                else:
                    query = '{0} where {1} is {2}'.format(
                        query, primary_key, str(entity_keys[0][0])
                    )

            result = self.query(query)

            # Fetch all results now. Doing so will cause them to populate the
            # relevant entities in the cache.
            result.all()

            # TODO: Should we check that all requested attributes were
            # actually populated? If some weren't would we mark that to avoid
            # repeated calls or perhaps raise an error?

    # TODO: Make atomic.
    def commit(self):
        '''Commit all local changes to the server.'''
        batch = []

        with self.auto_populating(False):
            for operation in self.recorded_operations:

                # Convert operation to payload.
                if isinstance(
                    operation, ftrack_api.operation.CreateEntityOperation
                ):
                    # At present, data payload requires duplicating entity
                    # type in data and also ensuring primary key added.
                    entity_data = {
                        '__entity_type__': operation.entity_type,
                    }
                    entity_data.update(operation.entity_key)
                    entity_data.update(operation.entity_data)

                    payload = {
                        'action': 'create',
                        'entity_type': operation.entity_type,
                        'entity_key': operation.entity_key.values(),
                        'entity_data': entity_data
                    }

                elif isinstance(
                    operation, ftrack_api.operation.UpdateEntityOperation
                ):
                    entity_data = {
                        # At present, data payload requires duplicating entity
                        # type.
                        '__entity_type__': operation.entity_type,
                        operation.attribute_name: operation.new_value
                    }

                    payload = {
                        'action': 'update',
                        'entity_type': operation.entity_type,
                        'entity_key': operation.entity_key.values(),
                        'entity_data': entity_data
                    }

                elif isinstance(
                    operation, ftrack_api.operation.DeleteEntityOperation
                ):
                    payload = {
                        'action': 'delete',
                        'entity_type': operation.entity_type,
                        'entity_key': operation.entity_key.values()
                    }

                else:
                    raise ValueError(
                        'Cannot commit. Unrecognised operation type {0} '
                        'detected.'.format(type(operation))
                    )

                batch.append(payload)

        # Optimise batch.
        # TODO: Might be better to perform these on the operations list instead
        # so all operation contextual information available.

        # If entity was created and deleted in one batch then remove all
        # payloads for that entity.
        created = set()
        deleted = set()

        for payload in batch:
            if payload['action'] == 'create':
                created.add(
                    (payload['entity_type'], str(payload['entity_key']))
                )

            elif payload['action'] == 'delete':
                deleted.add(
                    (payload['entity_type'], str(payload['entity_key']))
                )

        created_then_deleted = deleted.intersection(created)
        if created_then_deleted:
            optimised_batch = []
            for payload in batch:
                entity_type = payload.get('entity_type')
                entity_key = str(payload.get('entity_key'))

                if (entity_type, entity_key) in created_then_deleted:
                    continue

                optimised_batch.append(payload)

            batch = optimised_batch

        # Remove early update operations so that only last operation on
        # attribute is applied server side.
        updates_map = set()
        for payload in reversed(batch):
            if payload['action'] == 'update':
                for key, value in payload['entity_data'].items():
                    if key == '__entity_type__':
                        continue

                    identity = (
                        payload['entity_type'], str(payload['entity_key']), key
                    )
                    if identity in updates_map:
                        del payload['entity_data'][key]
                    else:
                        updates_map.add(identity)

        # Remove NOT_SET values from entity_data.
        for payload in batch:
            entity_data = payload.get('entity_data', {})
            for key, value in entity_data.items():
                if value is ftrack_api.symbol.NOT_SET:
                    del entity_data[key]

        # Remove payloads with redundant entity_data.
        optimised_batch = []
        for payload in batch:
            entity_data = payload.get('entity_data')
            if entity_data is not None:
                keys = entity_data.keys()
                if not keys or keys == ['__entity_type__']:
                    continue

            optimised_batch.append(payload)

        batch = optimised_batch

        # Collapse updates that are consecutive into one payload. Also, collapse
        # updates that occur immediately after creation into the create payload.
        optimised_batch = []
        previous_payload = None

        for payload in batch:
            if (
                previous_payload is not None
                and payload['action'] == 'update'
                and previous_payload['action'] in ('create', 'update')
                and previous_payload['entity_type'] == payload['entity_type']
                and previous_payload['entity_key'] == payload['entity_key']
            ):
                previous_payload['entity_data'].update(payload['entity_data'])
                continue

            else:
                optimised_batch.append(payload)
                previous_payload = payload

        batch = optimised_batch

        # Process batch.
        if batch:
            result = self._call(batch)

            # Clear all local values for committed attributes before proceeding
            # with merge. Otherwise it is possible for an immutable attribute
            # error to be bypassed.
            with self.operation_recording(False):
                for payload in batch:
                    if payload['action'] in ('create', 'update'):
                        # Retrieve entity from cache.
                        entity = self._get(
                            payload['entity_type'], payload['entity_key']
                        )

                        for key in payload['entity_data'].keys():
                            if key in ('__entity_type__', ):
                                continue

                            attribute = entity.attributes.get(key)
                            attribute.set_local_value(
                                entity, ftrack_api.symbol.NOT_SET
                            )

            # Process results merging into cache relevant data.
            for entry in result:

                if entry['action'] in ('create', 'update'):
                    # Merge returned entities into local cache.
                    self.merge(entry['data'])

                elif entry['action'] == 'delete':
                    # TODO: Detach entity - need identity returned?
                    # TODO: Expunge entity from cache.
                    pass

            # Clear operations.
            self.recorded_operations.clear()

    def _fetch_server_information(self):
        '''Return server information.'''
        result = self._call([{'action': 'query_server_information'}])
        return result[0]

    def _discover_plugins(self):
        '''Find and load plugins in search paths.

        Each discovered module should implement a register function that
        accepts this session as first argument. Typically the function should
        register appropriate event listeners against the session's event hub.

            def register(session):
                session.event_hub.subscribe(
                    'topic=ftrack.api.session.construct-entity-type',
                    construct_entity_type
                )

        '''
        ftrack_api.plugin.discover(self._plugin_paths, [self])

    def _fetch_schemas(self):
        '''Return schemas fetched from server.'''
        result = self._call([{'action': 'query_schemas'}])
        return result[0]

    def _build_entity_type_classes(self, schemas):
        '''Build default entity type classes.'''
        fallback_factory = ftrack_api.entity.factory.StandardFactory()
        classes = {}

        for schema in schemas:
            results = self.event_hub.publish(
                ftrack_api.event.base.Event(
                    topic='ftrack.api.session.construct-entity-type',
                    data=dict(
                        schema=schema,
                        schemas=schemas
                    )
                ),
                synchronous=True
            )

            results = [result for result in results if result is not None]

            if not results:
                self.logger.debug(
                    'Using default StandardFactory to construct entity type '
                    'class for "{0}"'.format(schema['id'])
                )
                entity_type_class = fallback_factory.create(schema)

            elif len(results) > 1:
                raise ValueError(
                    'Expected single entity type to represent schema "{0}" but '
                    'received {1} entity types instead.'
                    .format(schema['id'], len(results))
                )

            else:
                entity_type_class = results[0]

            classes[entity_type_class.entity_type] = entity_type_class

        return classes

    def _configure_locations(self):
        '''Configure locations.'''
        # First configure builtin locations, by injecting them into local cache.

        # Origin.
        location = self.create(
            'Location',
            data=dict(
                name='ftrack.origin',
                id=ftrack_api.symbol.ORIGIN_LOCATION_ID
            ),
            reconstructing=True
        )
        ftrack_api.mixin(
            location, ftrack_api.entity.location.OriginLocationMixin,
            name='OriginLocation'
        )
        location.accessor = ftrack_api.accessor.disk.DiskAccessor(prefix='')
        location.structure = ftrack_api.structure.origin.OriginStructure()
        location.priority = 100

        # Unmanaged.
        location = self.create(
            'Location',
            data=dict(
                name='ftrack.unmanaged',
                id=ftrack_api.symbol.UNMANAGED_LOCATION_ID
            ),
            reconstructing=True
        )
        ftrack_api.mixin(
            location, ftrack_api.entity.location.UnmanagedLocationMixin,
            name='UnmanagedLocation'
        )
        location.accessor = ftrack_api.accessor.disk.DiskAccessor(prefix='')
        location.structure = ftrack_api.structure.origin.OriginStructure()
        # location.resource_identifier_transformer = (
        #     ftrack_api.resource_identifier_transformer.internal.InternalResourceIdentifierTransformer(session)
        # )
        location.priority = 90

        # Review.
        location = self.create(
            'Location',
            data=dict(
                name='ftrack.review',
                id=ftrack_api.symbol.REVIEW_LOCATION_ID
            ),
            reconstructing=True
        )
        ftrack_api.mixin(
            location, ftrack_api.entity.location.UnmanagedLocationMixin,
            name='UnmanagedLocation'
        )
        location.accessor = ftrack_api.accessor.disk.DiskAccessor(prefix='')
        location.structure = ftrack_api.structure.origin.OriginStructure()
        location.priority = 110

        # Server.
        location = self.create(
            'Location',
            data=dict(
                name='ftrack.server',
                id=ftrack_api.symbol.SERVER_LOCATION_ID
            ),
            reconstructing=True
        )
        location.accessor = ftrack_api.accessor.server._ServerAccessor(
            session=self
        )
        location.structure = ftrack_api.structure.entity_id.EntityIdStructure()
        location.priority = 150

        # Next, allow further configuration of locations via events.
        self.event_hub.publish(
            ftrack_api.event.base.Event(
                topic='ftrack.api.session.configure-location',
                data=dict(
                    session=self
                )
            ),
            synchronous=True
        )

    def _call(self, data):
        '''Make request to server with *data*.'''
        url = self._server_url + '/api'
        headers = {
            'content-type': 'application/json',
            'accept': 'application/json'
        }
        data = self.encode(data, entity_attribute_strategy='modified_only')

        self.logger.debug(
            'Calling server {0} with {1!r}'.format(url, data)
        )

        response = self._request.post(
            url,
            headers=headers,
            data=data
        )

        self.logger.debug(
            'Call took: {0}'.format(response.elapsed.total_seconds())
        )

        self.logger.debug('Response: {0!r}'.format(response.text))
        try:
            result = self.decode(response.text)

        except Exception:
            error_message = (
                'Server reported error in unexpected format. Raw error was: {0}'
                .format(response.text)
            )
            self.logger.error(error_message)
            raise ftrack_api.exception.ServerError(error_message)

        else:
            if 'exception' in result:
                # Handle exceptions.
                error_message = 'Server reported error: {0}({1})'.format(
                    result['exception'], result['content']
                )
                self.logger.error(error_message)
                raise ftrack_api.exception.ServerError(error_message)

        return result

    def encode(self, data, entity_attribute_strategy='set_only'):
        '''Return *data* encoded as JSON formatted string.

        *entity_attribute_strategy* specifies how entity attributes should be
        handled. The following strategies are available:

        * *all* - Encode all attributes, loading any that are currently NOT_SET.
        * *set_only* - Encode only attributes that are currently set without
          loading any from the remote.
        * *modified_only* - Encode only attributes that have been modified
          locally.
        * *persisted_only* - Encode only remote (persisted) attribute values.

        '''
        entity_attribute_strategies = (
            'all', 'set_only', 'modified_only', 'persisted_only'
        )
        if entity_attribute_strategy not in entity_attribute_strategies:
            raise ValueError(
                'Unsupported entity_attribute_strategy "{0}". Must be one of '
                '{1}'.format(
                    entity_attribute_strategy,
                    ', '.join(entity_attribute_strategies)
                )
            )

        return json.dumps(
            data,
            sort_keys=True,
            default=functools.partial(
                self._encode,
                entity_attribute_strategy=entity_attribute_strategy
            )
        )

    def _encode(self, item, entity_attribute_strategy='set_only'):
        '''Return JSON encodable version of *item*.

        *entity_attribute_strategy* specifies how entity attributes should be
        handled. See :meth:`Session.encode` for available strategies.

        '''
        if isinstance(item, (arrow.Arrow, datetime.datetime, datetime.date)):
            return {
                '__type__': 'datetime',
                'value': item.isoformat()
            }

        if isinstance(item, ftrack_api.entity.base.Entity):
            data = self._entity_reference(item)

            with self.auto_populating(True):

                for attribute in item.attributes:
                    value = ftrack_api.symbol.NOT_SET

                    if entity_attribute_strategy == 'all':
                        value = attribute.get_value(item)

                    elif entity_attribute_strategy == 'set_only':
                        if attribute.is_set(item):
                            value = attribute.get_local_value(item)
                            if value is ftrack_api.symbol.NOT_SET:
                                value = attribute.get_remote_value(item)

                    elif entity_attribute_strategy == 'modified_only':
                        if attribute.is_modified(item):
                            value = attribute.get_local_value(item)

                    elif entity_attribute_strategy == 'persisted_only':
                        value = attribute.get_remote_value(item)

                    if value is not ftrack_api.symbol.NOT_SET:
                        if isinstance(
                            attribute, ftrack_api.attribute.ReferenceAttribute
                        ):
                            if isinstance(value, ftrack_api.entity.base.Entity):
                                value = self._entity_reference(value)

                        data[attribute.name] = value

            return data

        if isinstance(
            item, ftrack_api.collection.MappedCollectionProxy
        ):
            # Use proxied collection for serialisation.
            item = item.collection

        if isinstance(item, ftrack_api.collection.Collection):
            data = []
            for entity in item:
                data.append(self._entity_reference(entity))

            return data

        raise TypeError('{0!r} is not JSON serializable'.format(item))

    def _entity_reference(self, entity):
        '''Return reference to *entity*.

        Return a mapping containing the __entity_type__ of the entity along with
        the key, value pairs that make up it's primary key.

        '''
        reference = {
            '__entity_type__': entity.entity_type
        }
        with self.auto_populating(False):
            reference.update(ftrack_api.inspection.primary_key(entity))

        return reference

    def decode(self, string):
        '''Return decoded JSON *string* as Python object.'''
        with self.operation_recording(False):
            return json.loads(string, object_hook=self._decode)

    def _decode(self, item):
        '''Return *item* transformed into appropriate representation.'''
        if isinstance(item, collections.Mapping):
            if '__type__' in item:
                if item['__type__'] == 'datetime':
                    item = arrow.get(item['value'])

            elif '__entity_type__' in item:
                item = self._create(
                    item['__entity_type__'], item, reconstructing=True
                )

        return item

    def _get_locations(self, filter_inaccessible=True):
        '''Helper to returns locations ordered by priority.

        If *filter_inaccessible* is True then only accessible locations will be
        included in result.

        '''
        # Optimise this call.
        locations = self.query('Location')

        # Filter.
        if filter_inaccessible:
            locations = filter(
                lambda location: location.accessor,
                locations
            )

        # Sort by priority.
        locations = sorted(
            locations, key=lambda location: location.priority
        )

        return locations

    def pick_location(self, component=None):
        '''Return suitable location to use.

        If no *component* specified then return highest priority accessible
        location. Otherwise, return highest priority accessible location that
        *component* is available in.

        Return None if no suitable location could be picked.

        '''
        if component:
            return self.pick_locations([component])[0]

        else:
            locations = self._get_locations()
            if locations:
                return locations[0]
            else:
                return None

    def pick_locations(self, components):
        '''Return suitable locations for *components*.

        Return list of locations corresponding to *components* where each
        picked location is the highest priority accessible location for that
        component. If a component has no location available then its
        corresponding entry will be None.

        '''
        candidate_locations = self._get_locations()
        availabilities = self.get_component_availabilities(
            components, locations=candidate_locations
        )

        locations = []
        for component, availability in zip(components, availabilities):
            location = None

            for candidate_location in candidate_locations:
                if availability.get(candidate_location['id']) > 0.0:
                    location = candidate_location
                    break

            locations.append(location)

        return locations

    def create_component(
        self, path, data=None, location='auto'
    ):
        '''Create a new component from *path* with additional *data*

        .. note::

            This is a helper method. To create components manually use the
            standard :meth:`Session.create` method.

        *path* can be a string representing a filesystem path to the data to
        use for the component. The *path* can also be specified as a sequence
        string, in which case a sequence component with child components for
        each item in the sequence will be created automatically. The accepted
        format for a sequence is '{head}{padding}{tail} [{ranges}]'. For
        example::

            '/path/to/file.%04d.ext [1-5, 7, 8, 10-20]'

        .. seealso::

            `Clique documentation <http://clique.readthedocs.org>`_

        *data* should be a dictionary of any additional data to construct the
        component with (as passed to :meth:`Session.create`).

        If *location* is specified then automatically add component to that
        location. The default of 'auto' will automatically pick a suitable
        location to add the component to if one is available. To not add to any
        location specifiy locations as None.

        '''
        if data is None:
            data = {}

        if location == 'auto':
            # Check if the component name matches one of the ftrackreview
            # specific names. Add the component to the ftrack.review location if
            # so. This is used to not break backwards compatibility.
            if data.get('name') in (
                'ftrackreview-mp4', 'ftrackreview-webm', 'ftrackreview-image'
            ):
                location = self.get(
                    'Location', ftrack_api.symbol.REVIEW_LOCATION_ID
                )

            else:
                location = self.pick_location()

        try:
            collection = clique.parse(path)

        except ValueError:
            # Assume is a single file.
            if 'size' not in data:
                data['size'] = self._get_filesystem_size(path)

            data.setdefault('file_type', os.path.splitext(path)[-1])

            return self._create_component(
                'FileComponent', path, data, location
            )

        else:
            # Calculate size of container and members.
            member_sizes = {}
            container_size = data.get('size')

            if container_size is not None:
                if len(collection.indexes) > 0:
                    member_size = int(
                        round(container_size / len(collection.indexes))
                    )
                    for item in collection:
                        member_sizes[item] = member_size

            else:
                container_size = 0
                for item in collection:
                    member_sizes[item] = self._get_filesystem_size(item)
                    container_size += member_sizes[item]

            # Create sequence component
            container_path = collection.format('{head}{padding}{tail}')
            data.setdefault('padding', collection.padding)
            data.setdefault('file_type', os.path.splitext(container_path)[-1])

            container = self._create_component(
                'SequenceComponent', container_path, data, location
            )

            # Create member components for sequence.
            for member_path in collection:
                member_data = {
                    'name': collection.match(member_path).group('index'),
                    'container': container,
                    'size': member_sizes[member_path],
                    'file_type': os.path.splitext(member_path)[-1]
                }

                self._create_component(
                    'FileComponent', member_path, member_data, location
                )

            return container

    def _create_component(self, entity_type, path, data, location):
        '''Create and return component.

        See public function :py:func:`createComponent` for argument details.

        '''
        component = self.create(entity_type, data)

        # Add to special origin location so that it is possible to add to other
        # locations.
        origin_location = self.get(
            'Location', ftrack_api.symbol.ORIGIN_LOCATION_ID
        )
        origin_location.add_component(component, path, recursive=False)

        if location:
            location.add_component(component, origin_location, recursive=False)

        return component

    def _get_filesystem_size(self, path):
        '''Return size from *path*'''
        try:
            size = os.path.getsize(path)
        except OSError:
            size = 0

        return size

    def get_component_availability(self, component, locations=None):
        '''Return availability of *component*.

        If *locations* is set then limit result to availability of *component*
        in those *locations*.

        Return a dictionary of {location_id:percentage_availability}

        '''
        return self.get_component_availabilities(
            [component], locations=locations
        )[0]

    def get_component_availabilities(self, components, locations=None):
        '''Return availabilities of *components*.

        If *locations* is set then limit result to availabilities of
        *components* in those *locations*.

        Return a list of dictionaries of {location_id:percentage_availability}.
        The list indexes correspond to those of *components*.

        '''
        availabilities = []

        if locations is None:
            locations = self.query('Location')

        # Separate components into two lists, those that are containers and
        # those that are not, so that queries can be optimised.
        standard_components = []
        container_components = []

        for component in components:
            if 'members' in component.keys():
                container_components.append(component)
            else:
                standard_components.append(component)

        # Perform queries.
        if standard_components:
            self.populate(
                standard_components, 'component_locations.location_id'
            )

        if container_components:
            self.populate(
                container_components,
                'members, component_locations.location_id'
            )

        base_availability = {}
        for location in locations:
            base_availability[location['id']] = 0.0

        for component in components:
            availability = base_availability.copy()
            availabilities.append(availability)

            is_container = 'members' in component.keys()
            if is_container and len(component['members']):
                member_availabilities = self.get_component_availabilities(
                    component['members'], locations=locations
                )
                multiplier = 1.0 / len(component['members'])
                for member, member_availability in zip(
                    component['members'], member_availabilities
                ):
                    for location_id, ratio in member_availability.items():
                        availability[location_id] += (
                            ratio * multiplier
                        )
            else:
                for component_location in component['component_locations']:
                    location_id = component_location['location_id']
                    availability[location_id] = 100.0

            for location_id, percentage in availability.items():
                # Avoid quantization error by rounding percentage and clamping
                # to range 0-100.
                adjusted_percentage = round(percentage, 9)
                adjusted_percentage = max(0.0, min(adjusted_percentage, 100.0))
                availability[location_id] = adjusted_percentage

        return availabilities


class AutoPopulatingContext(object):
    '''Context manager for temporary change of session auto_populate value.'''

    def __init__(self, session, auto_populate):
        '''Initialise context.'''
        super(AutoPopulatingContext, self).__init__()
        self._session = session
        self._auto_populate = auto_populate
        self._current_auto_populate = None

    def __enter__(self):
        '''Enter context switching to desired auto populate setting.'''
        self._current_auto_populate = self._session.auto_populate
        self._session.auto_populate = self._auto_populate

    def __exit__(self, exception_type, exception_value, traceback):
        '''Exit context resetting auto populate to original setting.'''
        self._session.auto_populate = self._current_auto_populate


class OperationRecordingContext(object):
    '''Context manager for temporary change of session record_operations.'''

    def __init__(self, session, record_operations):
        '''Initialise context.'''
        super(OperationRecordingContext, self).__init__()
        self._session = session
        self._record_operations = record_operations
        self._current_record_operations = None

    def __enter__(self):
        '''Enter context.'''
        self._current_record_operations = self._session.record_operations
        self._session.record_operations = self._record_operations

    def __exit__(self, exception_type, exception_value, traceback):
        '''Exit context.'''
        self._session.record_operations = self._current_record_operations
