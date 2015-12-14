# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import ftrack_api.structure.base


class ClassicStructure(ftrack_api.structure.base.Structure):

    def _get_fragments(self, entity):
        session = entity.session
        component = session.query(
            'Component where id is "{0}"'.format(
                entity['id']
            )
        ).one()

        structure_names = [
            item['name']
            for item in component['version']['link'][1:-1]
        ]

        project_id = component['version']['link'][0]['id']
        project = session.get('Project', project_id)
        asset = component['version']['asset']

        version_number = 'v{0:03d}'.format(component['version']['version'])

        fragments = []
        fragments.append(project['name'])
        fragments.extend(structure_names)
        fragments.append(asset['name'])
        fragments.append(version_number)

        return fragments

    def get_resource_identifier(self, entity, context=None):
        if entity.entity_type in ('FileComponent',):
            container = entity['container']
            if container and container is not ftrack_api.symbol.NOT_SET:
                if container.entity_type in ('SequenceComponent',):
                    name = '{0}.{1}{2}'.format(
                        container['name'], entity['name'], entity['file_type']
                    )

                else:
                    name = entity['name'] + entity['file_type']

                fragments = self._get_fragments(container)

            else:
                name = entity['name'] + entity['file_type']
                fragments = self._get_fragments(entity)

            fragments.append(name)

        elif entity.entity_type in ('SequenceComponent',):
            fragments = self._get_fragments(entity)
            sequence_expression = self._get_sequence_expression(entity)
            fragments.append(
                '{}.{}{}'.format(
                    entity['name'], sequence_expression,
                    entity['file_type']
                )
            )

        elif entity.entity_type in ('ContainerComponent',):
            fragments = self._get_fragments(entity)

        resource_identifier = self.path_separator.join(
            fragments
        ).replace(' ', '_').lower()

        return resource_identifier
