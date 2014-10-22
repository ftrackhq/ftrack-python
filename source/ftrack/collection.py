# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import collections

import ftrack.exception
import ftrack.inspection


class Collection(collections.MutableSequence):
    '''A collection of entities.'''

    def __init__(self, entity, attribute, mutable=True, data=None):
        '''Initialise collection.'''
        self.entity = entity
        self.attribute = attribute
        self.mutable = mutable
        self._data = []

        if data is None:
            data = []

        self.extend(data)

    def _notify(self):
        '''Notify about modication.'''
        self.entity.session.set_state(self.entity, 'modified')

    def insert(self, index, item):
        '''Insert *item* at *index*.'''
        if not self.mutable:
            raise ftrack.exception.ImmutableCollectionError(self)

        if item in self:
            raise ftrack.exception.DuplicateItemInCollectionError(item, self)

        self._data.insert(index, item)
        self._notify()

    def __getitem__(self, index):
        '''Return item at *index*.'''
        return self._data[index]

    def __setitem__(self, index, item):
        '''Set *item* against *index*.'''
        if not self.mutable:
            raise ftrack.exception.ImmutableCollectionError(self)

        if item in self:
            raise ftrack.exception.DuplicateItemInCollectionError(item, self)

        self._data[index] = item
        self._notify()

    def __delitem__(self, index):
        '''Remove item at *index*.'''
        if not self.mutable:
            raise ftrack.exception.ImmutableCollectionError(self)

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
            ftrack.inspection.identity(entity)
            for entity in self
        ]

        other_identities = [
            ftrack.inspection.identity(entity)
            for entity in other
        ]

        return sorted(identities) == sorted(other_identities)

    def __ne__(self, other):
        '''Return whether this collection is not equal to *other*.'''
        return not self == other
