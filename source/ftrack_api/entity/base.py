# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import abc
import collections
import logging

import ftrack_api.symbol
import ftrack_api.attribute
import ftrack_api.inspection
import ftrack_api.exception
import ftrack_api.operation


class DynamicEntityTypeMetaclass(abc.ABCMeta):
    '''Custom metaclass to customise representation of dynamic classes.

    .. note::

        Derive from same metaclass as derived bases to avoid conflicts.

    '''
    def __repr__(self):
        '''Return representation of class.'''
        return '<dynamic ftrack class \'{0}\'>'.format(self.__name__)


class Entity(collections.MutableMapping):
    '''Base class for all entities.'''

    __metaclass__ = DynamicEntityTypeMetaclass

    entity_type = 'Entity'
    attributes = None
    primary_key_attributes = None
    default_projections = None

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
        super(Entity, self).__init__()
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.session = session

        if data is None:
            data = {}

        self.logger.debug(
            '{0} entity from {1!r}.'
            .format(
                ('Reconstructing' if reconstructing else 'Constructing'),
                data
            )
        )

        self._ignore_data_keys = ['__entity_type__']
        if not reconstructing:
            self._construct(data)
        else:
            self._reconstruct(data)

    def _construct(self, data):
        '''Construct from *data*.'''
        # Suspend operation recording so that all modifications can be applied
        # in single create operation. In addition, recording a modification
        # operation requires a primary key which may not be available yet.
        with self.session.operation_recording(False):

            # Data represents locally set values.
            for key, value in data.items():
                if key in self._ignore_data_keys:
                    continue

                attribute = self.__class__.attributes.get(key)
                if attribute is None:
                    self.logger.debug(
                        'Cannot populate {0!r} attribute as no such attribute '
                        'found on entity {1!r}.'.format(key, self)
                    )
                    continue

                attribute.set_local_value(self, value)

            # Set defaults for any unset local attributes.
            for attribute in self.__class__.attributes:
                if attribute.name not in data:
                    default_value = attribute.default_value
                    if callable(default_value):
                        default_value = default_value(self)

                    attribute.set_local_value(self, default_value)

    def _reconstruct(self, data):
        '''Reconstruct from *data*.'''
        # Data represents remote values.
        for key, value in data.items():
            if key in self._ignore_data_keys:
                continue

            attribute = self.__class__.attributes.get(key)
            if attribute is None:
                self.logger.debug(
                    'Cannot populate {0!r} attribute as no such attribute '
                    'found on entity {1!r}.'.format(key, self)
                )
                continue

            attribute.set_remote_value(self, value)

    def __repr__(self):
        '''Return representation of instance.'''
        return '<dynamic ftrack {0} object {1}>'.format(
            self.__class__.__name__, id(self)
        )

    def __str__(self):
        '''Return string representation of instance.'''
        with self.session.auto_populating(False):
            primary_key = ['Unknown']
            try:
                primary_key = ftrack_api.inspection.primary_key(self).values()
            except KeyError:
                pass

        return '<{0}({1})>'.format(
            self.__class__.__name__, ', '.join(primary_key)
        )

    def __hash__(self):
        '''Return hash representing instance.'''
        return hash(ftrack_api.inspection.identity(self))

    def __eq__(self, other):
        '''Return whether *other* is equal to this instance.

        .. note::

            Equality is determined by both instances having the same identity.
            Values of attributes are not considered.

        '''
        try:
            return (
                ftrack_api.inspection.identity(other)
                == ftrack_api.inspection.identity(self)
            )
        except (AttributeError, KeyError):
            return False

    def __getitem__(self, key):
        '''Return attribute value for *key*.'''
        attribute = self.__class__.attributes.get(key)
        if attribute is None:
            raise KeyError(key)

        return attribute.get_value(self)

    def __setitem__(self, key, value):
        '''Set attribute *value* for *key*.'''
        attribute = self.__class__.attributes.get(key)
        if attribute is None:
            raise KeyError(key)

        attribute.set_local_value(self, value)

    def __delitem__(self, key):
        '''Clear attribute value for *key*.

        .. note::

            Will not remove the attribute, but instead clear any local value
            and revert to the last known server value.

        '''
        attribute = self.__class__.attributes.get(key)
        attribute.set_local_value(self, ftrack_api.symbol.NOT_SET)

    def __iter__(self):
        '''Iterate over all attributes keys.'''
        for attribute in self.__class__.attributes:
            yield attribute.name

    def __len__(self):
        '''Return count of attributes.'''
        return len(self.__class__.attributes)

    def values(self):
        '''Return list of values.'''
        if self.session.auto_populate:
            self._populate_unset_scalar_attributes()

        return super(Entity, self).values()

    def items(self):
        '''Return list of tuples of (key, value) pairs.

        .. note::

            Will fetch all values from the server if not already fetched or set
            locally.

        '''
        if self.session.auto_populate:
            self._populate_unset_scalar_attributes()

        return super(Entity, self).items()

    def clear(self):
        '''Reset all locally modified attribute values.'''
        for attribute in self:
            del self[attribute]

    def merge(self, entity, merged=None):
        '''Merge *entity* attribute values and other data into this entity.

        Only merge values from *entity* that are not
        :attr:`ftrack_api.symbol.NOT_SET`.

        Return a list of changes made with each change being a mapping with
        the keys:

            * type - Either 'remote_attribute', 'local_attribute' or 'property'.
            * name - The name of the attribute / property modified.
            * old_value - The previous value.
            * new_value - The new merged value.

        '''
        if merged is None:
            merged = {}

        log_message = 'Merged {type} "{name}": {old_value!r} -> {new_value!r}'
        changes = []

        # Attributes.

        # Prioritise by type so that scalar values are set first. This should
        # guarantee that the attributes making up the identity of the entity
        # are merged before merging any collections that may have references to
        # this entity.
        attributes = collections.deque()
        for attribute in entity.attributes:
            if isinstance(attribute, ftrack_api.attribute.ScalarAttribute):
                attributes.appendleft(attribute)
            else:
                attributes.append(attribute)

        for other_attribute in attributes:
            attribute = self.attributes.get(other_attribute.name)

            # Local attributes.
            other_local_value = other_attribute.get_local_value(entity)
            if other_local_value is not ftrack_api.symbol.NOT_SET:
                local_value = attribute.get_local_value(self)
                if local_value != other_local_value:
                    merged_local_value = self.session.merge(
                        other_local_value, merged=merged
                    )

                    attribute.set_local_value(self, merged_local_value)
                    changes.append({
                        'type': 'local_attribute',
                        'name': attribute.name,
                        'old_value': local_value,
                        'new_value': merged_local_value
                    })
                    self.logger.debug(log_message.format(**changes[-1]))

            # Remote attributes.
            other_remote_value = other_attribute.get_remote_value(entity)
            if other_remote_value is not ftrack_api.symbol.NOT_SET:
                remote_value = attribute.get_remote_value(self)
                if remote_value != other_remote_value:
                    merged_remote_value = self.session.merge(
                        other_remote_value, merged=merged
                    )

                    attribute.set_remote_value(self, merged_remote_value)
                    changes.append({
                        'type': 'remote_attribute',
                        'name': attribute.name,
                        'old_value': remote_value,
                        'new_value': merged_remote_value
                    })
                    self.logger.debug(log_message.format(**changes[-1]))

        return changes

    def _populate_unset_scalar_attributes(self):
        '''Populate all unset scalar attributes in one query.'''
        projections = []
        for attribute in self.attributes:
            if isinstance(attribute, ftrack_api.attribute.ScalarAttribute):
                if attribute.get_remote_value(self) is ftrack_api.symbol.NOT_SET:
                    projections.append(attribute.name)

        if projections:
            self.session.populate([self], ', '.join(projections))
