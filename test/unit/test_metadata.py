# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import uuid

import ftrack_api


class TestMetadata(object):
    '''Class for testing metadata.'''

    def setup_method(self, method):
        '''Setup the test.'''
        self.session = ftrack_api.Session()
        name = 'projectname_{0}'.format(uuid.uuid1().hex)
        project_schemas = self.session.query('ProjectSchema')
        project = self.session.create('Project', {
            'name': name,
            'full_name': name + '_full',
            'project_schema': project_schemas[0]
        })

        self.sequence = self.session.create('Sequence', {
            'name': 'seq_1',
            'parent': project
        })
        self.session.commit()

    def test_query_metadata(self):
        '''Query metadata.'''
        metadata_key = uuid.uuid1().hex
        metadata_value = uuid.uuid1().hex
        self.sequence['metadata'][metadata_key] = metadata_value
        self.session.commit()

        results = self.session.query(
            'Sequence where metadata.key is {0}'.format(metadata_key)
        )

        assert len(results) == 1
        assert self.sequence['id'] == results[0]['id']

        results = self.session.query(
            'Sequence where metadata.value is {0}'.format(metadata_value)
        )

        assert len(results) == 1
        assert self.sequence['id'] == results[0]['id']

        results = self.session.query(
            'Sequence where metadata.key is {0} and '
            'metadata.value is {1}'.format(metadata_key, metadata_value)
        )

        assert len(results) == 1
        assert self.sequence['id'] == results[0]['id']

    def test_set_get_metadata_from_different_sessions(self):
        '''Get and set metadata using different sessions.'''
        metadata_key = uuid.uuid1().hex
        metadata_value = uuid.uuid1().hex
        self.sequence['metadata'][metadata_key] = metadata_value
        self.session.commit()

        new_session = ftrack_api.Session()

        sequence = new_session.query(
            'Sequence where id is {0}'.format(self.sequence['id'])
        )[0]

        assert sequence['metadata'][metadata_key] == metadata_value

        sequence['metadata'][metadata_key] = uuid.uuid1().hex

        new_session.commit()

        new_session = ftrack_api.Session()

        sequence = new_session.query(
            'Sequence where id is {0}'.format(self.sequence['id'])
        )[0]

        assert sequence['metadata'][metadata_key] != metadata_value

    def test_get_set_multiple_metadata(self):
        '''Get and set multiple metadata.'''
        self.sequence['metadata'] = {
            'key1': 'value1',
            'key2': 'value2'
        }
        self.session.commit()

        assert set(self.sequence['metadata'].keys()) == set(['key1', 'key2'])

        new_session = ftrack_api.Session()

        sequence = new_session.query(
            'Sequence where id is {0}'.format(self.sequence['id'])
        )[0]

        assert set(sequence['metadata'].keys()) == set(['key1', 'key2'])
