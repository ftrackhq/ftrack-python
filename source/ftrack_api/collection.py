# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import collections

import ftrack_api.exception
import ftrack_api.inspection
import ftrack_api.symbol
import ftrack_api.operation


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

    def _notify(self, old_value):
        '''Notify about modification.'''
        if self._suspend_notifications:
            return

        # Record operation.
        if self.entity.session.record_operations:
            self.entity.session.recorded_operations.push(
                ftrack_api.operation.UpdateEntityOperation(
                    self.entity.entity_type,
                    ftrack_api.inspection.primary_key(self.entity),
                    self.attribute.name,
                    old_value,
                    self._data
                )
            )

    def insert(self, index, item):
        '''Insert *item* at *index*.'''
        if not self.mutable:
            raise ftrack_api.exception.ImmutableCollectionError(self)

        if item in self:
            raise ftrack_api.exception.DuplicateItemInCollectionError(
                item, self
            )

        old_value = self._data[:]
        self._data.insert(index, item)
        self._notify(old_value)

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

        old_value = self._data[:]
        self._data[index] = item
        self._notify(old_value)

    def __delitem__(self, index):
        '''Remove item at *index*.'''
        if not self.mutable:
            raise ftrack_api.exception.ImmutableCollectionError(self)

        old_value = self._data[:]
        del self._data[index]
        self._notify(old_value)

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
