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


class MappedCollectionProxy(collections.MutableMapping):
    '''A mapped collection of entities.

    Proxy a standard :class:`Collection` as a mapping where certain attributes
    from the entities in the collection are mapped to key, value pairs.

    For example::

        >>> collection = [Metadata(key='foo', value='bar'), ...]
        >>> mapped = MappedCollectionProxy(
        ...     collection, create_metadata,
        ...     key_attribute='key', value_attribute='value'
        ... )
        >>> print mapped['foo']
        'bar'
        >>> mapped['bam'] = 'biz'
        >>> print mapped.collection[-1]
        Metadata(key='bam', value='biz')

    '''

    def __init__(
        self, collection, creator, key_attribute, value_attribute
    ):
        '''Initialise collection.'''
        self.collection = collection
        self.creator = creator
        self.key_attribute = key_attribute
        self.value_attribute = value_attribute

    @property
    def mutable(self):
        '''Return whether collection is mutable.'''
        return self.collection.mutable

    @mutable.setter
    def mutable(self, value):
        '''Set whether collection is mutable to *value*.'''
        self.collection.mutable = value

    @property
    def attribute(self):
        '''Return attribute bound to.'''
        return self.collection.attribute

    @attribute.setter
    def attribute(self, value):
        '''Set bound attribute to *value*.'''
        self.collection.attribute = value

    def _get_entity_by_key(self, key):
        '''Return entity instance with matching *key* from collection.'''
        for entity in self.collection:
            if entity[self.key_attribute] == key:
                return entity

        raise KeyError(key)

    def __getitem__(self, key):
        '''Return value for *key*.'''
        entity = self._get_entity_by_key(key)
        return entity[self.value_attribute]

    def __setitem__(self, key, value):
        '''Set *value* for *key*.'''
        try:
            entity = self._get_entity_by_key(key)
        except KeyError:
            data = {
                self.key_attribute: key,
                self.value_attribute: value
            }
            entity = self.creator(self, data)
            self.collection.append(entity)
        else:
            entity[self.value_attribute] = value

    def __delitem__(self, key):
        '''Remove and delete *key*.

        .. note::

            The associated entity will be deleted as well.

        '''
        for index, entity in enumerate(self.collection):
            if entity[self.key_attribute] == key:
                break
        else:
            raise KeyError(key)

        del self.collection[index]
        entity.session.delete(entity)

    def __iter__(self):
        '''Iterate over all keys.'''
        keys = set()
        for entity in self.collection:
            keys.add(entity[self.key_attribute])

        return iter(keys)

    def __len__(self):
        '''Return count of keys.'''
        keys = set()
        for entity in self.collection:
            keys.add(entity[self.key_attribute])

        return len(keys)
