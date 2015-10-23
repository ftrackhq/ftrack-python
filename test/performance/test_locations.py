# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import datetime
import sys
import time

import ftrack_api

import base


class AddImagesequenceComponents(base.PerformanceTest):
    '''Add an image sequence with 25 components.'''

    def setup(self):
        '''Setup tests.'''
        self.session = ftrack_api.Session()
        self.my_version = self.session.query('AssetVersion').first()

    def run(self):
        '''Run tests.'''
        self.component = self.my_version.create_component(
            '/path/to/file.%d.jpg [1001-1025]',
            data={
                'name': 'animAnimIO-{0}'.format(
                    time.mktime(datetime.datetime.now().timetuple())
                )
            },
            location='auto'
        )
        self.session.commit()

    def teardown(self):
        '''Teardown tests.'''
        self.session.delete(self.component)
        self.session.commit()


def main(arguments=None):
    '''Run all tests.'''

    for case in ('time', 'profile'):
        test = AddImagesequenceComponents()
        test.setup()
        getattr(test, case)()
        test.teardown()

if __name__ == '__main__':
    main(sys.argv[1:])
    raise SystemExit()
