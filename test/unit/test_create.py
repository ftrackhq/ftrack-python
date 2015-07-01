# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import uuid

import ftrack_api


class TestCreateProject(object):
    '''Class for testing create.'''

    def setup_method(self, method):
        '''Setup the test.'''
        self.session = ftrack_api.Session()

    def test_create_empty_project(self):
        '''Create an empty project.'''
        name = 'projectname_{0}'.format(uuid.uuid1().hex)
        project_schemas = self.session.query('ProjectSchema')
        project = self.session.create('Project', {
            'name': name,
            'full_name': name + '_full',
            'project_schema': project_schemas[0]
        })
        self.session.commit()

        results = self.session.query(
            'Project where id is {0}'.format(project['id'])
        )

        assert len(results) == 1
        assert results[0]['name'] == name
        assert results[0]['project_schema_id'] == project_schemas[0]['id']

    def test_create_project(self):
        '''Create a project with sequences, shots and tasks.'''
        name = 'projectname_{0}'.format(uuid.uuid1().hex)
        project_schema = self.session.query('ProjectSchema').first()
        default_shot_status = project_schema.get_statuses('Shot')[0]
        default_task_type = project_schema.get_types('Task')[0]
        default_task_status = project_schema.get_statuses(
            'Task', default_task_type['id']
        )[0]

        project = self.session.create('Project', {
            'name': name,
            'full_name': name + '_full',
            'project_schema': project_schema
        })

        for sequence_number in range(1, 5):
            sequence = self.session.create('Sequence', {
                'name': 'seq_{0}'.format(sequence_number),
                'parent': project
            })

            for shot_number in range(1, 5):
                shot = self.session.create('Shot', {
                    'name': '{0}0'.format(shot_number).zfill(3),
                    'parent': sequence,
                    'status': default_shot_status
                })

                for task_number in range(1, 5):
                    self.session.create('Task', {
                        'name': 'task_{0}'.format(task_number),
                        'parent': shot,
                        'status': default_task_status,
                        'type': default_task_type
                    })

        self.session.commit()

        results = self.session.query(
            'Task where project_id is {0}'.format(project['id'])
        )

        assert len(results) == 64
