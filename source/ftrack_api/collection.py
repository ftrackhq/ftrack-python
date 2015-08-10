# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import collections
import copy

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

        # Set initial dataset.
        if data is None:
            data = []

        with self.entity.session.operation_recording(False):
            self.extend(data)

    def __copy__(self):
        '''Return shallow copy.

        .. note::

            To maintain expectations on usage, the shallow copy will include a
            shallow copy of the underlying data store.

        '''
        cls = self.__class__
        copied_instance = cls.__new__(cls)
        copied_instance.__dict__.update(self.__dict__)
        copied_instance._data = copy.copy(self._data)

        return copied_instance

    def _notify(self, old_value):
        '''Notify about modification.'''
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


class MappedCollectionProxy(collections.MutableMapping):
    pass


class KeyValueMappedCollectionProxy(MappedCollectionProxy):
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

    def __copy__(self):
        '''Return shallow copy.

        .. note::

            To maintain expectations on usage, the shallow copy will include a
            shallow copy of the underlying collection.

        '''
        cls = self.__class__
        copied_instance = cls.__new__(cls)
        copied_instance.__dict__.update(self.__dict__)
        copied_instance.collection = copy.copy(self.collection)

        return copied_instance

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


CONFIGURATIONS = None


def get_configurations(entity):
    global CONFIGURATIONS
    if CONFIGURATIONS is None:
        CONFIGURATIONS = entity.session.query(
            'select key, top_id, id, entity_key from '
            'CustomAttributeConfiguration'
        ).all()

    return CONFIGURATIONS


class CustomAttributeCollectionProxy(MappedCollectionProxy):
    '''A mapped collection of custom attribute value entities.'''

    def __init__(
        self, collection
    ):
        '''Initialise collection.'''
        self.collection = collection
        self.key_attribute = 'custom_attribute_configuration_id'
        self.value_attribute = 'value'
        import traceback
        traceback.print_stack(limit=10)

    def __copy__(self):
        '''Return shallow copy.

        .. note::

            To maintain expectations on usage, the shallow copy will include a
            shallow copy of the underlying collection.

        '''
        cls = self.__class__
        copied_instance = cls.__new__(cls)
        copied_instance.__dict__.update(self.__dict__)
        copied_instance.collection = copy.copy(self.collection)

        return copied_instance

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

    def _get_entity_configurations(self):
        '''Return all configurations for current collection entity.'''
        entity = self.collection.entity
        entity_type = None
        project_id = None
        object_type_id = None

        if 'object_type_id' in entity.keys():
            project_id = entity['project_id']
            entity_type = 'task'
            object_type_id = entity['object_type_id']

        if entity.entity_type == 'AssetVersion':
            project_id = entity['asset']['parent']['project_id']
            entity_type = 'assetversion'

        if entity.entity_type == 'Project':
            project_id = entity['id']
            entity_type = 'show'

        if entity.entity_type == 'User':
            entity_type = 'user'

        if entity_type is None:
            raise ValueError(
                'Entity {!r} not supported.'.format(entity)
            )

        configurations = []
        for configuration in get_configurations(entity):
            if (
                configuration['entity'] == entity_type and
                configuration['top_id'] in (project_id, None),
                configuration['entity_key'] == object_type_id
            ):
                configurations.append(configuration)

        return configurations

    def _get_keys(self):
        '''Return a list of all keys.'''
        keys = []
        for configuration in self._get_entity_configurations():
            keys.append(configuration['key'])

        return keys

    def _get_entity_by_key(self, key):
        '''Return entity instance with matching *key* from collection.'''
        translated_key = self.encode(key)
        for entity in self.collection:
            if entity[self.key_attribute] == translated_key:
                return entity

        return None

    def encode(self, data):
        '''Encode a key to a custom attribute configuration id.'''
        for configuration in self._get_entity_configurations():
            if data == configuration['key']:
                return configuration['id']

        raise KeyError(data)

    def decode(self, data):
        '''Decode a custom attribute configuration id to a key.'''
        entity = self.collection.entity
        for configuration in get_configurations(entity):
            if configuration['id'] == data:
                return configuration['key']

        raise KeyError(data)

    def __getitem__(self, key):
        '''Return value for *key*.'''
        entity = self._get_entity_by_key(key)

        if entity:
            return entity[self.value_attribute]

        for configuration in self._get_entity_configurations():
            if configuration['key'] == key:
                return configuration['default']

        raise KeyError(key)

    def __setitem__(self, key, value):
        '''Set *value* for *key*.'''
        custom_attribute_value = self._get_entity_by_key(key)

        if custom_attribute_value:
            custom_attribute_value[self.value_attribute] = value
        else:
            entity = self.collection.entity
            session = entity.session
            data = {
                self.key_attribute: self.encode(key),
                self.value_attribute: value,
                'entity_id': entity['id']
            }

            # Make sure to use the currently active collection. This is
            # necessary since a merge might have replaced the current one.
            self.collection.entity['custom_attributes'].collection.append(
                session.create('CustomAttributeValue', data)
            )

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
        keys = self._get_keys()
        return iter(keys)

    def __len__(self):
        '''Return count of keys.'''
        keys = self._get_keys()
        return len(keys)
