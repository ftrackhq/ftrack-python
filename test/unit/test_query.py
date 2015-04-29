# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import uuid

import ftrack_api


class TestQuery(object):
    '''Class for testing query.'''

    def setup_method(self, method):
        '''Setup the test.'''
        self.session = ftrack_api.Session()
        self.project = self._create_project()

    def teardown_method(self, method):
        '''Teardown the test.'''
        self.session.delete(self.project)
        self.session.commit()

    def _create_project(self):
        '''Create a project with tasks and return their names.'''
        name = 'projectname_{0}'.format(uuid.uuid1().hex)
        project_schema = self.session.query('ProjectSchema')[0]
        default_task_type = project_schema.get_types('Task')[0]
        default_task_status = project_schema.get_statuses(
            'Task', default_task_type['id']
        )[0]

        project = self.session.create('Project', {
            'name': name,
            'full_name': name + '_full',
            'project_schema': project_schema
        })

        for task_number in range(0, 4):
            self.session.create('Task', {
                'name': uuid.uuid1().hex,
                'parent': project,
                'status': default_task_status,
                'type': default_task_type
            })

        self.session.commit()

        return project

    def  test_query_tasks_by_name(self):
        '''Query tasks by name.'''
        tasks = self.session.query('Task where project_id is "{}"'.format(
            self.project['id'])
        )
        task_names = [task['name'] for task in tasks]
        task_ids = [task['id'] for task in tasks]

        result = self.session.query(
            'Task where name is {0}'.format(task_names[0])
        )

        assert result[0]['name'] == task_names[0] and len(result) == 1

        result = self.session.query(
            'Task where name is "{name}" and id is "{id}"'.format(
                name=task_names[0], id=task_ids[0]
            )
        )

        assert result[0]['name'] == task_names[0] and len(result) == 1

        result = self.session.query(
            'Task where name in ("{0}", "{1}")'.format(
                task_names[0], task_names[1]
            )
        )

        assert (
            len(result) == 2 and
            result[0]['name'] in task_names and
            result[1]['name'] in task_names
        )

        result = self.session.query(
            'Task where name is "{0}" or name is "{1}"'.format(
                task_names[0], task_names[1]
            )
        )

        assert (
            len(result) == 2 and
            result[0]['name'] in task_names and
            result[1]['name'] in task_names
        )
