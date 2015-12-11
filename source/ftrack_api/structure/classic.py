# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import ftrack_api.structure.base


class ClassicStructure(ftrack_api.structure.base.Structure):

    def get_resource_identifier(self, entity, context=None):

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
        project = session.query(
            'Project where id is {}'.format(project_id)
        ).one()
        asset = component['version']['asset']

        version_number = 'v{0:03d}'.format(component['version']['version'])

        file_name = component['name'] + component['file_type']

        fragments = []
        fragments.append(project['name'])
        fragments.extend(structure_names)
        fragments.append(asset['name'])
        fragments.append(version_number)
        fragments.append(file_name)

        resource_identifier = self.path_separator.join(fragments)

        return resource_identifier
