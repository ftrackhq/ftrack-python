# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import collections

import ftrack_api.exception
import ftrack_api.inspection
import ftrack_api.symbol


class Collection(collections.MutableSequence):
    '''A collection of entities.'''

    def __init__(self, entity, attribute, mutable=True, data=None):
        '''Initialise collection.'''
        self.entity = entity
        self.attribute = attribute
        self.mutable = mutable
        self._data = []
        self._suspend_notifications = False

        # Set initial dataset.
        # Suspend notifications whilst setting initial data to avoid incorrect
        # state changes on entity.
        if data is None:
            data = []

        self._suspend_notifications = True
        try:
            self.extend(data)
        finally:
            self._suspend_notifications = False

    def _notify(self):
        '''Notify about modification.'''
        if self._suspend_notifications:
            return

        self.entity.state = ftrack_api.symbol.MODIFIED

    def insert(self, index, item):
        '''Insert *item* at *index*.'''
        if not self.mutable:
            raise ftrack_api.exception.ImmutableCollectionError(self)

        if item in self:
            raise ftrack_api.exception.DuplicateItemInCollectionError(
                item, self
            )

        self._data.insert(index, item)
        self._notify()

    def __getitem__(self, index):
        '''Return item at *index*.'''
        return self._data[index]

    def __setitem__(self, index, item):
        '''Set *item* against *index*.'''
        if not self.mutable:
            raise ftrack_api.exception.ImmutableCollectionError(self)

        try:
            existing_index = self.index(item)
        except ValueError:
            pass
        else:
            if index != existing_index:
                raise ftrack_api.exception.DuplicateItemInCollectionError(
                    item, self
                )

        self._data[index] = item
        self._notify()

    def __delitem__(self, index):
        '''Remove item at *index*.'''
        if not self.mutable:
            raise ftrack_api.exception.ImmutableCollectionError(self)

        del self._data[index]
        self._notify()

    def __len__(self):
        '''Return count of items.'''
        return len(self._data)

    def __eq__(self, other):
        '''Return whether this collection is equal to *other*.'''
        if not isinstance(other, Collection):
            return False

        identities = [
            ftrack_api.inspection.identity(entity)
            for entity in self
        ]
        other_identities = [
            ftrack_api.inspection.identity(entity)
            for entity in other
        ]

        return sorted(identities) == sorted(other_identities)

    def __ne__(self, other):
        '''Return whether this collection is not equal to *other*.'''
        return not self == other


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
