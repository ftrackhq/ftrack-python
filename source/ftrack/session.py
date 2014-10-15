# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import json
import logging
import collections

import requests
import requests.auth

import ftrack.exception
import ftrack.entity
import ftrack.inspection
import ftrack.cache
import ftrack.symbol
import ftrack.query


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

    def __init__(self, server_url, api_key, api_user, auto_populate=True):
        '''Initialise session.

        *server_url* should be the URL of the ftrack server to connect to
        including any port number.

        *api_key* should be the API key to use for authentication whilst
        *api_user* should be the username of the user in ftrack to record
        operations against.

        If *auto_populate* is True (the default), then accessing entity
        attributes will cause them to be automatically fetched from the server
        if they are not already. This flag can be changed on the session
        directly at any time.

        '''
        super(Session, self).__init__()
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self._server_url = server_url
        self._api_key = api_key
        self._api_user = api_user

        self._batches = {
            'read': [],
            'write': []
        }

        # TODO: Make cache configurable.
        self._key_maker = ftrack.cache.EntityKeyMaker()
        self._cache = ftrack.cache.MemoryCache()

        self._states = dict(
            created=collections.OrderedDict(),
            modified=collections.OrderedDict(),
            deleted=collections.OrderedDict()
        )

        self._request = requests.Session()
        self._request.auth = SessionAuthentication(
            self._api_key, self._api_user
        )

        # TODO: Make schemas read-only and non-mutable (or at least without
        # rebuilding types)?
        self.schemas = self._fetch_schemas()
        self.types = self._build_entity_type_classes(self.schemas)

        self.auto_populate = auto_populate

    def close(self):
        '''Close session clearing all locally stored data.'''
        # TODO: Run final batches?
        self._states['created'].clear()
        self._states['modified'].clear()
        self._states['deleted'].clear()
        self._request.close()

    def auto_populating(self, auto_populate):
        '''Temporarily set auto populate to *auto_populate*.

        The current setting will be restored automatically when done.

        Example::

            with session.auto_populating(False):
                print entity['name']

        '''
        return AutoPopulatingContext(self, auto_populate)

    @property
    def created(self):
        '''Return list of newly created entities.'''
        return self._states['created'].values()

    @property
    def modified(self):
        '''Return list of locally modified entities.'''
        return self._states['modified'].values()

    @property
    def deleted(self):
        '''Return list of deleted entities.'''
        return self._states['deleted'].values()

    def set_state(self, entity, state):
        '''Set *entity* *state*.

        Transition from current state to new state.

        Raise :exc:`ftrack.exception.InvalidStateError` if new state is invalid.

        .. note::

            Transitioning from 'created' or 'deleted' to 'modified' is not an
            error, but will not change state.

        '''
        identity = id(entity)
        current_state = self.get_state(entity)

        if current_state == state:
            return

        if current_state in ('created', 'deleted'):
            if state == 'modified':
                # Not an error, but no point marking as modified.
                return

        if current_state == 'deleted':
            raise ftrack.exception.InvalidStateTransitionError(
                current_state, state, entity
            )

        if current_state == 'modified' and state != 'deleted':
            raise ftrack.exception.InvalidStateTransitionError(
                current_state, state, entity
            )

        if current_state:
            del self._states[current_state][identity]

        if state:
            self._states[state][identity] = entity

    def get_state(self, entity):
        '''Return entity *state*.'''
        identity = id(entity)
        for state, entities in self._states.iteritems():
            if identity in entities:
                return state

        return None

    def create(self, entity_type, data=None):
        '''Create and return an entity of *entity_type* with initial *data*.

        If specified, *data* should be a dictionary of key, value pairs that
        should be used to populate attributes on the entity.

        # TODO: What should happen to unrecognised keys? Should they just be
        # set as normal attributes?

        '''
        return self._create(entity_type, data, reconstructing=False)

    def _create(self, entity_type, data, reconstructing):
        '''Create and return an entity of *entity_type* with initial *data*.

        If *reconstructing* is True then will merge into any existing entity.

        '''
        try:
            EntityTypeClass = self.types[entity_type]
        except KeyError:
            raise ftrack.exception.UnrecognisedEntityTypeError(entity_type)

        entity = EntityTypeClass(self, data=data, reconstructing=reconstructing)

        # Check for existing instance of entity in cache.
        key = self._key_maker.key(entity)
        try:
            existing = self._cache.get(key)
        except KeyError:
            existing = None

        if existing:
            if not reconstructing:
                raise ftrack.exception.NotUniqueError(
                    'Entity with same identity {0} already exists in session.'
                    .format(key)
                )
            else:
                # Merge attributes.
                for attribute in entity.attributes:
                    value = attribute.get_remote_value(entity)
                    if value is not ftrack.symbol.NOT_SET:
                        existing_attribute = existing.attributes.get(
                            attribute.name
                        )
                        existing_attribute.set_remote_value(existing, value)

        else:
            # Record new instance in cache.
            self._cache.set(key, entity)

        return entity

    def ensure(self, entity_type, data):
        '''Ensure entity of *entity_type* with *data* exists.'''

    def delete(self, entity):
        '''Mark *entity* for deletion.'''
        self.set_state(entity, 'deleted')

    def get(self, entity_type, entity_key):
        '''Return entity of *entity_type* with unique *entity_key*.'''

    def query(self, expression):
        '''Query against remote data according to *expression*.

        *expression* is not executed directly. Instead return an
        :class:`ftrack.query.QueryResult` instance that will execute remote
        call on access.

        '''
        query_result = ftrack.query.QueryResult(self, expression)
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
        return results[0]['data']

    def populate(self, entities, projections, background=False):
        '''Populate *entities* with attributes specified by *projections*.

        if *background* is True make request without blocking and populate
        entities when result received.

        Any locally set values included in the *projections* will not be
        overwritten with the retrieved remote value. If this 'synchronise'
        behaviour is required, first clear the relevant values on the entity by
        setting them to :attr:`ftrack.symbol.NOT_SET`. Deleting the key will
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
        if not isinstance(entities, (list, tuple)):
            entities = [entities]

        # TODO: How to handle a mixed collection of different entity types.
        # Should probably fail, but need to consider handling hierarchies such
        # as User and Group both deriving from Resource.
        # Actually, could just proceed and ignore projections that are
        # not present in entity type.

        entities_to_process = []

        for entity in entities:
            if self.get_state(entity) == 'created':
                # Created entities that are not yet persisted have no remote
                # values. Don't raise an error here as it is reasonable to
                # iterate over an entities properties and see that some of them
                # are NOT_SET.
                continue

            entities_to_process.append(entity)

        if entities_to_process:
            reference_entity = entities_to_process[0]
            entity_type = ftrack.inspection.entity_type(reference_entity)
            query = 'select {0} from {1}'.format(projections, entity_type)

            primary_key_definition = reference_entity.schema['primary_key']
            if len(primary_key_definition) > 1:
                # TODO: Handle composite primary key using a syntax of
                # (pka, pkb) in ((v1a,v1b), (v2a, v2b))
                raise ValueError('Composite primary keys not supported.')

            primary_key = primary_key_definition[0]

            entity_keys = [
                ftrack.inspection.primary_key(entity)[0]
                for entity in entities_to_process
            ]

            if len(entity_keys) > 1:
                query = '{0} where {1} in ({2})'.format(
                    query, primary_key, ','.join(map(str, entity_keys))
                )
            else:
                query = '{0} where {1} is {2}'.format(
                    query, primary_key, str(entity_keys[0])
                )

            self.logger.debug('Query: {0!r}'.format(query))
            result = self.query(query)

            # Fetch all results now. Doing so will cause them to populate the
            # relevant entities in the cache.
            result.all()

    # TODO: Make atomic.
    def commit(self):
        '''Commit all local changes to the server.'''
        # Add all deletions in order.
        for entity in self.deleted:
            self._batches['write'].append({
                'action': 'delete',
                'entity_type': ftrack.inspection.entity_type(entity),
                'entity_key': ftrack.inspection.primary_key(entity)
            })

        # Add all creations in order.
        for entity in self.created:
            self._batches['write'].append({
                'action': 'create',
                'entity_type': ftrack.inspection.entity_type(entity),
                'entity_data': entity
            })

        # Add all modifications.
        for entity in self.modified:
            data = {}
            for attribute in entity.attributes:
                if attribute.is_modified(entity):
                    new_value = attribute.get_local_value(entity)
                    data[attribute.name] = new_value

            if data:
                self._batches['write'].append({
                    'action': 'update',
                    'entity_type': ftrack.inspection.entity_type(entity),
                    'entity_key': ftrack.inspection.primary_key(entity),
                    'entity_data': data
                })

        batch = self._batches['write']
        if batch:
            results = self._call(batch)

            # Process operation results.
            for result in results:
                if result['action'] == 'create':
                    # Result already merged into session via decode. Just need
                    # to mark attributes as loaded which will happen in
                    # _post_commit.
                    pass

            self._post_commit()

    def _post_commit(self):
        '''Reset following successful commit.'''
        del self._batches['write'][:]

        for entity in self.created:
            for attribute in entity.attributes:
                attribute.set_local_value(entity, ftrack.symbol.NOT_SET)

        for entity in self.modified:
            for attribute in entity.attributes:
                attribute.set_local_value(entity, ftrack.symbol.NOT_SET)

        self._states['created'].clear()
        self._states['modified'].clear()
        self._states['deleted'].clear()

    def _fetch_schemas(self):
        '''Return schemas fetched from server.'''
        return []

    def _build_entity_type_classes(self, schemas):
        '''Build default entity type classes.'''
        classes = {}

        # TODO: Order by mro hierarchy to ensure parent classes constructed
        # first.
        for schema in schemas:
            entity_type_class = ftrack.entity.class_factory(schema)
            classes[entity_type_class.__name__] = entity_type_class

        return classes

    def _call(self, data):
        '''Make request to server with *data*.'''
        url = self._server_url + '/api'
        headers = {
            'content-type': 'application/json'
        }
        data = self.encode(data)

        self.logger.debug(
            'Calling server {0} with {1}'.format(url, data)
        )

        response = self._request.post(
            url,
            headers=headers,
            data=data
        )

        self.logger.debug(
            'Call took: {0}'.format(response.elapsed.total_seconds())
        )

        if response.status_code != 200:
            # TODO: Process error.
            raise Exception('Failed!')

        else:
            result = self.decode(response.text)

            if 'exception' in result:
                # Handle exceptions.
                raise ftrack.exception.ServerError(result['content'])

            else:
                # TODO: Process result.
                # Is there where entity merge should happen to centralise it?
                pass

        return result

    def encode(self, data):
        '''Return *data* encoded as JSON formatted string.'''
        return json.dumps(data, default=self._encode)

    def _encode(self, item):
        '''Return JSON encodable version of *item*.'''
        if isinstance(item, ftrack.entity.Entity):
            data = {}
            for attribute in item.attributes:
                if attribute.is_modified(item):
                    # TODO: Handle Collections as list of identities.
                    data[attribute.name] = attribute.get_local_value(item)

            return data

        raise TypeError('{0!r} is not JSON serializable'.format(item))

    def decode(self, string):
        '''Return decoded JSON *string* as Python object.'''
        return json.loads(string, object_hook=self._decode)

    def _decode(self, item):
        '''Return *item* transformed into appropriate representation.'''
        if isinstance(item, collections.Mapping):
            if '__type__' in item:
                item = self._load_entity(item)

        return item

    def _load_entity(self, entity_data):
        '''Load *entity_data* into local entity.

        If no matching entity exists then create it.

        *entity_data* must contain a '__type__' key that matches a registered
        entity type class and also the required primary key values for that
        type.

        Return entity.

        '''
        entity_type = str(entity_data.pop('__type__'))
        entity = self._create(entity_type, entity_data, reconstructing=True)

        # TODO: Should entity be given a 'persisted' state?

        return entity


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
