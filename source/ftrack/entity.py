# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import sys
import abc
import uuid
import collections
import logging

import ftrack.symbol
import ftrack.attribute


def class_factory(schema):
    '''Create entity class from *schema*.'''
    logger = logging.getLogger(__name__ + '.class_factory')

    entity_type = schema['id']
    class_name = entity_type
    class_bases = schema.get('bases', list())
    if not class_bases:
        class_bases = [Entity]

    class_namespace = dict()

    # Build attributes for class.
    attributes = ftrack.attribute.Attributes()
    immutable = schema.get('immutable', [])
    for name, fragment in schema.get('properties', {}).items():
        mutable = name not in immutable

        default = fragment.get('default', ftrack.symbol.NOT_SET)
        if default == '{uid}':
            default = lambda instance: str(uuid.uuid4())

        data_type = fragment.get('type', ftrack.symbol.NOT_SET)

        if data_type is not ftrack.symbol.NOT_SET:

            if data_type in (
                'string', 'boolean', 'integer', 'number'
            ):
                # Basic scalar attribute.
                if data_type == 'number':
                    data_type = 'float'

                if data_type == 'string':
                    data_format = fragment.get('format')
                    if data_format == 'date-time':
                        data_type = 'datetime'

                attribute = ftrack.attribute.ScalarAttribute(
                    name, data_type=data_type, default_value=default,
                    mutable=mutable
                )
                attributes.add(attribute)

            elif data_type == 'array':
                # Collection attribute.
                # reference = fragment.get('$ref', ftrack.symbol.NOT_SET)
                attribute = ftrack.attribute.CollectionAttribute(
                    name, mutable=mutable
                )
                attributes.add(attribute)

            else:
                logger.debug(
                    'Skipping {0}.{1} attribute with unrecognised data type {2}'
                    .format(class_name, name, data_type)
                )
        else:
            # Reference attribute.
            reference = fragment.get('$ref', ftrack.symbol.NOT_SET)
            if reference is not ftrack.symbol.NOT_SET:
                attribute = ftrack.attribute.ReferenceAttribute(name, reference)
                attributes.add(attribute)

    default_projections = schema.get('default_projections', [])

    # Construct class.
    class_namespace['entity_type'] = entity_type
    class_namespace['attributes'] = attributes
    class_namespace['primary_key_attributes'] = schema['primary_key'][:]
    class_namespace['default_projections'] = default_projections

    cls = type(
        str(class_name),  # type doesn't accept unicode.
        tuple(class_bases),
        class_namespace
    )

    return cls


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
        '''Initialise entity.'''
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

        if not reconstructing:
            # Mark as newly created for later commit.
            # Done here so that entity has correct state, otherwise would
            # receive a state of "modified" following setting of attribute
            # values from *data*.
            self.session.set_state(self, 'created')

            # Data represents locally set values.
            for key, value in data.items():
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
                if not attribute.name in data:
                    default_value = attribute.default_value
                    if callable(default_value):
                        default_value = default_value(self)

                    attribute.set_local_value(self, default_value)

        else:
            # Data represents remote values.
            for key, value in data.items():
                attribute = self.__class__.attributes.get(key)
                if attribute is None:
                    self.logger.debug(
                        'Cannot populate {0!r} attribute as no such attribute '
                        'found on entity {1!r}.'.format(key, self)
                    )
                    continue

                attribute.set_remote_value(self, value)

        # Assert that primary key is set. Suspend auto populate temporarily to
        # avoid infinite recursion if primary key values are not present.
        with self.session.auto_populating(False):
            self.primary_key

    def __repr__(self):
        '''Return representation of instance.'''
        return '<dynamic ftrack {0} object at {1:#0{2}x}>'.format(
            self.__class__.__name__, id(self),
            '18' if sys.maxsize > 2**32 else '10'
        )

    def __hash__(self):
        '''Return hash representing instance.'''
        return hash(self.identity)

    def __eq__(self, other):
        '''Return whether *other* is equal to this instance.

        .. note::

            Equality is determined by both instances having the same identity.
            Values of attributes are not considered.

        '''
        return other.identity == self.identity

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
        attribute.set_local_value(self, ftrack.symbol.NOT_SET)

    def __iter__(self):
        '''Iterate over all attributes keys.'''
        for attribute in self.__class__.attributes:
            yield attribute.name

    def __len__(self):
        '''Return count of attributes.'''
        return len(self.__class__.attributes)

    @property
    def identity(self):
        '''Return unique identity.'''
        return (
            self.entity_type,
            self.primary_key
        )

    @property
    def primary_key(self):
        '''Return primary key values as a tuple.'''
        primary_key = []
        for name in self.primary_key_attributes:
            value = self[name]
            if value is ftrack.symbol.NOT_SET:
                raise KeyError(
                    'Missing required value for primary key attribute "{0}" on '
                    'entity {1}.'.format(name, self)
                )

            primary_key.append(str(value))

        return tuple(primary_key)

    def values(self):
        '''Return list of values.'''
        # Optimisation: Populate all missing attributes in one query.
        if self.session.auto_populate:
            self._populate_unset_remote_values()

        return super(Entity, self).values()

    def items(self):
        '''Return list of tuples of (key, value) pairs.

        .. note::

            Will fetch all values from the server if not already fetched or set
            locally.

        '''
        # Optimisation: Populate all missing attributes in one query.
        if self.session.auto_populate:
            self._populate_unset_remote_values()

        return super(Entity, self).items()

    def clear(self):
        '''Reset all locally modified attribute values.'''
        for attribute in self:
            del self[attribute]

    def _populate_unset_remote_values(self):
        '''Populate all unset remote values in one query.'''
        projections = []
        for attribute in self.attributes:
            if attribute.get_remote_value(self) is ftrack.symbol.NOT_SET:
                projections.append(attribute.name)

        if projections:
            self.session.populate([self], ', '.join(projections))
