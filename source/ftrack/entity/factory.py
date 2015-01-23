# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import logging
import uuid

import ftrack.attribute
import ftrack.entity.base
import ftrack.symbol


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
        specified, default to :class:`ftrack.entity.base.Entity`.

        '''
        entity_type = schema['id']
        class_name = entity_type

        class_bases = bases
        if class_bases is None:
            class_bases = [ftrack.entity.base.Entity]

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

                elif data_type == 'dict':
                    attribute = ftrack.attribute.DictionaryAttribute(
                        name, schema=fragment, mutable=mutable
                    )
                    attributes.add(attribute)

                else:
                    self.logger.debug(
                        'Skipping {0}.{1} attribute with unrecognised data '
                        'type {2}'.format(class_name, name, data_type)
                    )
            else:
                # Reference attribute.
                reference = fragment.get('$ref', ftrack.symbol.NOT_SET)
                if reference is not ftrack.symbol.NOT_SET:
                    attribute = ftrack.attribute.ReferenceAttribute(
                        name, reference
                    )
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
