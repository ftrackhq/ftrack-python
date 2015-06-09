# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import sys
import collections

import ftrack_api.symbol
import ftrack_api.exception
import ftrack_api.collection
import ftrack_api.inspection
import ftrack_api.operation


class Attributes(object):
    '''Collection of properties accessible by name.'''

    def __init__(self, attributes=None):
        super(Attributes, self).__init__()
        self._data = dict()
        if attributes is not None:
            for attribute in attributes:
                self.add(attribute)

    def add(self, attribute):
        '''Add *attribute*.'''
        existing = self._data.get(attribute.name, None)
        if existing:
            raise ftrack_api.exception.NotUniqueError(
                'Attribute with name {0} already added as {1}'
                .format(attribute.name, existing)
            )

        self._data[attribute.name] = attribute

    def remove(self, attribute):
        '''Remove attribute.'''
        self._data.pop(attribute.name)

    def get(self, name):
        '''Return attribute by name.'''
        return self._data.get(name, None)

    def keys(self):
        '''Return list of attribute names.'''
        return self._data.keys()

    def __contains__(self, item):
        '''Return whether *item* present.'''
        if not isinstance(item, Attribute):
            return False

        return item.name in self._data

    def __iter__(self):
        '''Return iterator over attributes.'''
        return self._data.itervalues()

    def __len__(self):
        '''Return count of attributes.'''
        return len(self._data)


class Attribute(object):
    '''A name and value pair persisted remotely.'''

    def __init__(
        self, name, default_value=ftrack_api.symbol.NOT_SET, mutable=True
    ):
        '''Initialise attribute with *name*.

        *default_value* represents the default value for the attribute. It may
        be a callable. It is not used within the attribute when providing
        values, but instead exists for other parts of the system to reference.

        If *mutable* is set to False then the local value of the attribute on an
        entity can only be set when both the existing local and remote values
        are :attr:`ftrack_api.symbol.NOT_SET`. The exception to this is when the
        target value is also :attr:`ftrack_api.symbol.NOT_SET`.

        '''
        super(Attribute, self).__init__()
        self._name = name
        self._mutable = mutable
        self.default_value = default_value

        self._local_key = 'local'
        self._remote_key = 'remote'

    def __repr__(self):
        '''Return representation of entity.'''
        return '<{0}.{1}({2}) object at {3}>'.format(
            self.__module__,
            self.__class__.__name__,
            self.name,
            id(self)
        )

    def get_entity_storage(self, entity):
        '''Return attribute storage on *entity* creating if missing.'''
        storage_key = '_ftrack_attribute_storage'
        storage = getattr(entity, storage_key, None)
        if storage is None:
            storage = collections.defaultdict(
                lambda:
                {
                    self._local_key: ftrack_api.symbol.NOT_SET,
                    self._remote_key: ftrack_api.symbol.NOT_SET
                }
            )
            setattr(entity, storage_key, storage)

        return storage

    @property
    def name(self):
        '''Return name.'''
        return self._name

    @property
    def mutable(self):
        '''Return whether attribute is mutable.'''
        return self._mutable

    def get_value(self, entity):
        '''Return current value for *entity*.

        If a value was set locally then return it, otherwise return last known
        remote value. If no remote value yet retrieved, make a request for it
        via the session and block until available.

        '''
        value = self.get_local_value(entity)
        if value is not ftrack_api.symbol.NOT_SET:
            return value

        value = self.get_remote_value(entity)
        if value is not ftrack_api.symbol.NOT_SET:
            return value

        if not entity.session.auto_populate:
            return value

        self.populate_remote_value(entity)
        return self.get_remote_value(entity)

    def get_local_value(self, entity):
        '''Return locally set value for *entity*.'''
        storage = self.get_entity_storage(entity)
        return storage[self.name][self._local_key]

    def get_remote_value(self, entity):
        '''Return remote value for *entity*.

        .. note::

            Only return locally stored remote value, do not fetch from remote.

        '''
        storage = self.get_entity_storage(entity)
        return storage[self.name][self._remote_key]

    def set_local_value(self, entity, value):
        '''Set local *value* for *entity*.'''
        if (
            not self.mutable
            and self.is_set(entity)
            and value is not ftrack_api.symbol.NOT_SET
        ):
            raise ftrack_api.exception.ImmutableAttributeError(self)

        old_value = self.get_local_value(entity)

        storage = self.get_entity_storage(entity)
        storage[self.name][self._local_key] = value

        # Record operation.
        if entity.session.record_operations:
            entity.session.recorded_operations.push(
                ftrack_api.operation.UpdateEntityOperation(
                    entity.entity_type,
                    ftrack_api.inspection.primary_key(entity),
                    self.name,
                    old_value,
                    value
                )
            )

    def set_remote_value(self, entity, value):
        '''Set remote *value*.

        .. note::

            Only set locally stored remote value, do not persist to remote.

        '''
        storage = self.get_entity_storage(entity)
        storage[self.name][self._remote_key] = value

    def populate_remote_value(self, entity):
        '''Populate remote value for *entity*.'''
        entity.session.populate([entity], self.name)

    def is_modified(self, entity):
        '''Return whether local value set and differs from remote.

        .. note::

            Will not fetch remote value so may report True even when values
            are the same on the remote.

        '''
        local_value = self.get_local_value(entity)
        remote_value = self.get_remote_value(entity)
        return (
            local_value is not ftrack_api.symbol.NOT_SET
            and local_value != remote_value
        )

    def is_set(self, entity):
        '''Return whether a value is set for *entity*.'''
        return any([
            self.get_local_value(entity) is not ftrack_api.symbol.NOT_SET,
            self.get_remote_value(entity) is not ftrack_api.symbol.NOT_SET
        ])


class ScalarAttribute(Attribute):
    '''Represent a scalar value.'''

    def __init__(self, name, data_type, **kw):
        '''Initialise property.'''
        super(ScalarAttribute, self).__init__(name, **kw)
        self.data_type = data_type


class ReferenceAttribute(Attribute):
    '''Reference another entity.'''

    def __init__(self, name, entity_type, **kw):
        '''Initialise property.'''
        super(ReferenceAttribute, self).__init__(name, **kw)
        self.entity_type = entity_type

    def populate_remote_value(self, entity):
        '''Populate remote value for *entity*.

        As attribute references another entity, use that entity's configured
        default projections to auto populate useful attributes when loading.

        '''
        reference_entity_type = entity.session.types[self.entity_type]
        default_projections = reference_entity_type.default_projections

        projections = []
        if default_projections:
            for projection in default_projections:
                projections.append('{0}.{1}'.format(self.name, projection))
        else:
            projections.append(self.name)

        entity.session.populate([entity], ', '.join(projections))

    def is_modified(self, entity):
        '''Return whether a local value has been set and differs from remote.

        .. note::

            Will not fetch remote value so may report True even when values
            are the same on the remote.

        '''
        local_value = self.get_local_value(entity)
        remote_value = self.get_remote_value(entity)

        if local_value is ftrack_api.symbol.NOT_SET:
            return False

        if remote_value is ftrack_api.symbol.NOT_SET:
            return True

        if (
            ftrack_api.inspection.identity(local_value)
            != ftrack_api.inspection.identity(remote_value)
        ):
            return True

        return False


class CollectionAttribute(Attribute):
    '''Represent a collection of other entities.'''

    def get_value(self, entity):
        '''Return current value for *entity*.

        If a value was set locally then return it, otherwise return last known
        remote value. If no remote value yet retrieved, make a request for it
        via the session and block until available.

        .. note::

            As value is a collection that is mutable, will transfer a remote
            value into the local value on access if no local value currently
            set.

        '''
        super(CollectionAttribute, self).get_value(entity)

        # Conditionally, copy remote value into local value so that it can be
        # mutated without side effects.
        local_value = self.get_local_value(entity)
        remote_value = self.get_remote_value(entity)
        if (
            local_value is ftrack_api.symbol.NOT_SET
            and isinstance(remote_value, ftrack_api.collection.Collection)
        ):
            try:
                with entity.session.operation_recording(False):
                    self.set_local_value(entity, remote_value[:])
            except ftrack_api.exception.ImmutableAttributeError:
                pass

        return self.get_local_value(entity)

    def set_local_value(self, entity, value):
        '''Set local *value* for *entity*.'''
        if value is not ftrack_api.symbol.NOT_SET:
            value = self._adapt_to_collection(entity, value)
            value.mutable = self.mutable

        super(CollectionAttribute, self).set_local_value(entity, value)

    def set_remote_value(self, entity, value):
        '''Set remote *value*.

        .. note::

            Only set locally stored remote value, do not persist to remote.

        '''
        if value is not ftrack_api.symbol.NOT_SET:
            value = self._adapt_to_collection(entity, value)
            value.mutable = False

        super(CollectionAttribute, self).set_remote_value(entity, value)

    def _adapt_to_collection(self, entity, value):
        '''Adapt *value* to a Collection instance on *entity*.'''
        if not isinstance(value, ftrack_api.collection.Collection):
            value = ftrack_api.collection.Collection(entity, self, data=value)
        else:
            if not value.attribute is self:
                raise ftrack_api.exception.AttributeError(
                    'Collection already bound to a different attribute'
                )

        return value


class DictionaryAttributeCollection(object):
    '''Class representing a dictionary collection.'''

    def __init__(self, entity, name, schema):
        '''Initialise collection from *entity*, *name* and *schema*.'''
        self._entity = entity
        self._name = name
        self._store = {}
        self._is_store_loaded = False

        self._schema = schema
        keys = self._schema.get('keys', {})
        self._key_property = keys.get('key', 'key')
        self._value_property = keys.get('value', 'value')
        self._foreign_key_property = keys.get('parent_id', 'parent_id')
        self._class = self._schema.get('items').get('$ref')

    def _get_store(self):
        '''Return the store loaded with data.'''
        self._load_store()
        return self._store

    def _load_store(self):
        '''Populate store with all remote values.'''
        if self._is_store_loaded:
            return

        results = self._entity.session.query(
            '{0} where {1} = {2}'.format(
                self._class,
                self._foreign_key_property,
                self._entity['id']
            )
        )

        for key_value_object in results:
            key = key_value_object[self._key_property]
            if key not in self._store:
                self._store[key] = key_value_object

        self._is_store_loaded = True

    def _get(self, key):
        '''Return object by *key* or raise KeyError.'''
        try:
            return self._get_store()[key]

        except KeyError:
            raise KeyError(
                '{0} key {1} was not found for {2}'.format(
                    self._name, key, self._entity
                )
            )

    def __getitem__(self, key):
        '''Return value for *key*.'''
        return self._get(key)[self._value_property]

    def __setitem__(self, key, value):
        '''Set *value* for *key*.'''
        try:
            key_value_object = self._get(key)

        except KeyError:
            data = {
                self._foreign_key_property: self._entity['id'],
                self._key_property: key,
                self._value_property: value
            }
            data.update(self._schema.get('defaults', {}))
            key_value_object = self._entity.session.create(self._class, data)
            self._store[key] = key_value_object

        else:
            key_value_object[self._value_property] = value

    def __delitem__(self, key):
        '''Delete *key*.'''
        self._entity.session.delete(self._get(key))
        self._get_store().pop(key)

    def keys(self):
        '''Return keys for all objects in collection.'''
        return self._get_store().keys()

    def items(self):
        '''Return list of tuples.'''
        result = []
        for index, key_value_object in self._get_store().items():
            result.append((index, key_value_object[self._value_property]))

        return result

    def replace(self, data):
        '''Replace collection with *data*.'''
        # Delete.
        for key in self._get_store().keys():
            if key not in data:
                del self[key]

        for key, value in data.items():
            self[key] = value


class DictionaryAttribute(Attribute):
    '''Represent a dictionary attribute.'''

    def __init__(self, name, schema, **kw):
        '''Initialise property.'''
        super(DictionaryAttribute, self).__init__(name, **kw)
        self._collections = {}
        self._schema = schema

    def _getCollection(self, entity):
        '''Return collection for *entity*.'''
        primary_key = tuple(ftrack_api.inspection.primary_key(entity).values())
        if primary_key not in self._collections:
            key_value_collection = DictionaryAttributeCollection(
                entity=entity,
                name=self._name,
                schema=self._schema
            )
            self._collections[primary_key] = key_value_collection

        return self._collections[primary_key]

    def get_value(self, entity):
        '''Return collection for *entity*.'''
        return self._getCollection(entity)

    def set_local_value(self, entity, value):
        '''Update collection for *entity* with *value*.'''
        if value == ftrack_api.symbol.NOT_SET:
            return

        self._getCollection(entity).replace(value)
