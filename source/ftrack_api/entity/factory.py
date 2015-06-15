# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import logging
import uuid
import functools

import ftrack_api.attribute
import ftrack_api.entity.base
import ftrack_api.entity.location
import ftrack_api.entity.component
import ftrack_api.entity.asset_version
import ftrack_api.entity.project_schema
import ftrack_api.entity.job
import ftrack_api.symbol


class Factory(object):
    '''Entity class factory.'''

    def __init__(self):
        '''Initialise factory.'''
        super(Factory, self).__init__()
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

    def create(self, schema, bases=None):
        '''Create and return entity class from *schema*.

        *bases* should be a list of bases to give the constructed class. If not
        specified, default to :class:`ftrack_api.entity.base.Entity`.

        '''
        entity_type = schema['id']
        class_name = entity_type

        class_bases = bases
        if class_bases is None:
            class_bases = [ftrack_api.entity.base.Entity]

        class_namespace = dict()

        # Build attributes for class.
        attributes = ftrack_api.attribute.Attributes()
        immutable = schema.get('immutable', [])
        for name, fragment in schema.get('properties', {}).items():
            mutable = name not in immutable

            default = fragment.get('default', ftrack_api.symbol.NOT_SET)
            if default == '{uid}':
                default = lambda instance: str(uuid.uuid4())

            data_type = fragment.get('type', ftrack_api.symbol.NOT_SET)

            if data_type is not ftrack_api.symbol.NOT_SET:

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

                    attribute = self.create_scalar_attribute(
                        class_name, name, mutable, default, data_type
                    )
                    if attribute:
                        attributes.add(attribute)

                elif data_type == 'array':
                    attribute = self.create_collection_attribute(
                        class_name, name, mutable
                    )
                    if attribute:
                        attributes.add(attribute)

                elif data_type == 'mapped_array':
                    reference = fragment.get('items', {}).get('$ref')
                    if not reference:
                        self.logger.debug(
                            'Skipping {0}.{1} mapped_array attribute that does '
                            'not define a schema reference.'
                            .format(class_name, name)
                        )
                        continue

                    attribute = self.create_mapped_collection_attribute(
                        class_name, name, mutable, reference
                    )
                    if attribute:
                        attributes.add(attribute)

                else:
                    self.logger.debug(
                        'Skipping {0}.{1} attribute with unrecognised data '
                        'type {2}'.format(class_name, name, data_type)
                    )
            else:
                # Reference attribute.
                reference = fragment.get('$ref', ftrack_api.symbol.NOT_SET)
                if reference is ftrack_api.symbol.NOT_SET:
                    self.logger.debug(
                        'Skipping {0}.{1} mapped_array attribute that does '
                        'not define a schema reference.'
                        .format(class_name, name)
                    )
                    continue

                attribute = self.create_reference_attribute(
                    class_name, name, mutable, reference
                )
                if attribute:
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

    def create_scalar_attribute(
        self, class_name, name, mutable, default, data_type
    ):
        '''Return appropriate scalar attribute instance.'''
        return ftrack_api.attribute.ScalarAttribute(
            name, data_type=data_type, default_value=default, mutable=mutable
        )

    def create_reference_attribute(self, class_name, name, mutable, reference):
        '''Return appropriate reference attribute instance.'''
        return ftrack_api.attribute.ReferenceAttribute(
            name, reference, mutable=mutable
        )

    def create_collection_attribute(self, class_name, name, mutable):
        '''Return appropriate collection attribute instance.'''
        return ftrack_api.attribute.CollectionAttribute(
            name, mutable=mutable
        )

    def create_mapped_collection_attribute(
        self, class_name, name, mutable, reference
    ):
        '''Return appropriate mapped collection attribute instance.'''
        self.logger.debug(
            'Skipping {0}.{1} mapped_array attribute that has '
            'no implementation defined for reference {3}.'
            .format(class_name, name, reference)
        )


def default_task_status(entity):
    '''Return default task status entity for *entity*.'''
    return entity.session.query('TaskStatus')[0]


def default_task_type(entity):
    '''Return default task type entity for *entity*.'''
    return entity.session.query('TaskType')[0]


def default_task_priority(entity):
    '''Return default task priority entity for *entity*.'''
    return entity.session.query('PriorityType')[0]


class StandardFactory(Factory):
    '''Standard entity class factory.'''

    def create(self, schema, bases=None):
        '''Create and return entity class from *schema*.'''
        # Customise classes.
        if schema['id'] == 'ProjectSchema':
            cls = super(StandardFactory, self).create(
                schema, bases=[ftrack_api.entity.project_schema.ProjectSchema]
            )

        elif schema['id'] == 'Location':
            cls = super(StandardFactory, self).create(
                schema, bases=[ftrack_api.entity.location.Location]
            )

        elif schema['id'] == 'AssetVersion':
            cls = super(StandardFactory, self).create(
                schema, bases=[ftrack_api.entity.asset_version.AssetVersion]
            )

        elif schema['id'].endswith('Component'):
            cls = super(StandardFactory, self).create(
                schema, bases=[ftrack_api.entity.component.Component]
            )

        elif schema['id'].endswith('Job'):
            cls = super(StandardFactory, self).create(
                schema, bases=[ftrack_api.entity.job.Job]
            )

        else:
            cls = super(StandardFactory, self).create(schema, bases=bases)

        # Add dynamic default values to appropriate attributes so that end
        # users don't need to specify them each time.
        if schema['id'] in ('Episode', 'Sequence'):
            cls.attributes.get('status').default_value = default_task_status

        if schema['id'] in (
            'Episode', 'Sequence', 'Shot', 'AssetBuild', 'Task'
        ):
            cls.attributes.get('priority').default_value = default_task_priority

        if schema['id'] in ('Episode', 'Sequence', 'Shot'):
            cls.attributes.get('type').default_value = default_task_type

        return cls

    def create_mapped_collection_attribute(
        self, class_name, name, mutable, reference
    ):
        '''Return appropriate mapped collection attribute instance.'''
        creator = None
        key_attribute = None
        value_attribute = None

        if reference == 'Metadata':

            def create_metadata(proxy, data, reference):
                '''Return metadata for *data*.'''
                entity = proxy.collection.entity
                session = entity.session
                data.update({
                    'parent_id': entity['id'],
                    'parent_type': entity.entity_type
                })
                return session.create(reference, data)

            creator = functools.partial(
                create_metadata, reference=reference
            )
            key_attribute = 'key'
            value_attribute = 'value'

        if creator is None:
            self.logger.debug(
                'Skipping {0}.{1} mapped_array attribute that has '
                'no creator defined for reference {3}.'
                .format(class_name, name, reference)
            )
            return

        if key_attribute is None:
            self.logger.debug(
                'Skipping {0}.{1} mapped_array attribute that has '
                'no key_attribute defined for reference {3}.'
                .format(class_name, name, reference)
            )
            return

        if value_attribute is None:
            self.logger.debug(
                'Skipping {0}.{1} mapped_array attribute that has '
                'no value_attribute defined for reference {3}.'
                .format(class_name, name, reference)
            )
            return

        return ftrack_api.attribute.MappedCollectionAttribute(
            name, creator, key_attribute, value_attribute,
            mutable=mutable
        )
