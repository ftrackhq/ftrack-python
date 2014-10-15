# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import sys
import collections

import ftrack.symbol
import ftrack.inspection
import ftrack.exception


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
            raise ftrack.exception.NotUniqueError(
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

    def values(self):
        '''Return list of attribute entitys.'''
        return self._data.values()

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
        self, name, default_value=ftrack.symbol.NOT_SET
    ):
        '''Initialise attribute with *name*.'''
        super(Attribute, self).__init__()
        self._name = name
        self.default_value = default_value

        self._local_key = 'local'
        self._remote_key = 'remote'

    def __repr__(self):
        '''Return representation of entity.'''
        return '<{0}.{1}({2}) object at {3:#0{4}x}>'.format(
            self.__module__,
            self.__class__.__name__,
            self.name,
            id(self),
            '18' if sys.maxsize > 2**32 else '10'
        )

    def get_entity_storage(self, entity):
        '''Return attribute storage on *entity* creating if missing.'''
        # TODO: Make thread-safe.
        storage_key = '_ftrack_attribute_storage'
        storage = getattr(entity, storage_key, None)
        if storage is None:
            storage = collections.defaultdict(
                lambda:
                {
                    self._local_key: ftrack.symbol.NOT_SET,
                    self._remote_key: ftrack.symbol.NOT_SET
                }
            )
            setattr(entity, storage_key, storage)

        return storage

    @property
    def name(self):
        '''Return name.'''
        return self._name

    def get_value(self, entity):
        '''Return current value for *entity*.

        If a value was set locally then return it, otherwise return last known
        remote value. If no remote value yet retrieved, make a request for it
        via the session and block until available.

        '''
        value = self.get_local_value(entity)
        if value is not ftrack.symbol.NOT_SET:
            return value

        value = self.get_remote_value(entity)
        if value is not ftrack.symbol.NOT_SET:
            return value

        if not entity.session.auto_populate:
            return value

        # Fetch remote value and set on entity via attached session.
        # TODO: Is there a way to decouple this tight binding?
        entity.session.populate([entity], self.name)

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
        '''Set local *value* for *entity*.

        If *mark* is True then mark *entity* as modified in associated session.

        '''
        storage = self.get_entity_storage(entity)
        storage[self.name][self._local_key] = value

        # Add to modified session list.
        # TODO: Use events?
        if self.is_modified(entity):
            entity.session.set_state(entity, 'modified')

    def set_remote_value(self, entity, value):
        '''Set remote *value*.

        .. note::

            Only set locally stored remote value, do not persist to remote.

        '''
        storage = self.get_entity_storage(entity)
        storage[self.name][self._remote_key] = value

    def is_modified(self, entity):
        '''Return whether local value set and differs from remote.

        .. note::

            Will not fetch remote value so may report True even when values
            are the same on the remote.

        '''
        local_value = self.get_local_value(entity)
        remote_value = self.get_remote_value(entity)
        return (
            local_value is not ftrack.symbol.NOT_SET
            and local_value != remote_value
        )

    def is_set(self, entity):
        '''Return whether a value is set for *entity*.'''
        return any([
            self.get_local_value(entity) is not ftrack.symbol.NOT_SET,
            self.get_remote_value(entity) is not ftrack.symbol.NOT_SET
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

    def is_modified(self, entity):
        '''Return whether a local value has been set and differs from remote.

        .. note::

            Will not fetch remote value so may report True even when values
            are the same on the remote.

        '''
        local_value = self.get_local_value(entity)
        remote_value = self.get_remote_value(entity)

        if local_value is ftrack.symbol.NOT_SET:
            return False

        if remote_value is ftrack.symbol.NOT_SET:
            return True

        if (
            ftrack.inspection.identity(local_value)
            != ftrack.inspection.identity(remote_value)
        ):
            return True

        return False


class CollectionAttribute(Attribute):
    '''Represent a collection of other entities.'''
