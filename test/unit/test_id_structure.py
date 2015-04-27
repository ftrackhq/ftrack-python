# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import ftrack_api
import ftrack_api.structure.id


class TestIdStructure(object):
    '''Test id structure.'''

    def setup_method(self, method):
        '''Setup the test.'''

    def teardown_method(self, method):
        '''Teardown the test.'''

    def test_get_resource_identifier(self):
        '''Get resource identifier from structure.'''
        session = ftrack_api.Session()
        file_component = session.create('FileComponent', {
            'name': 'my_component_name',
            'file_type': '.png'
        })

        structure = ftrack_api.structure.id.IdStructure(prefix='/path')

        resource_identifier = structure.get_resource_identifier(file_component)

        assert resource_identifier.startswith('path/')
        assert resource_identifier.endswith(file_component['id'][4:] + '.png')

        sequence_component = session.create('SequenceComponent', {
            'name': 'my sequence component'
        })

        file_component = session.create('FileComponent', {
            'name': 'file_component_name',
            'container': sequence_component,
            'file_type': '.jpg'
        })

        resource_identifier = structure.get_resource_identifier(
            file_component
        )

        assert resource_identifier.startswith('path/')
        assert resource_identifier.endswith(
            sequence_component['id'][4:] + '/file.file_component_name.jpg'
        )
