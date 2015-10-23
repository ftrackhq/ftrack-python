# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import pstats
import time

try:
    import cProfile as profile
except ImportError:
    import profile


def print_test(decorated_function):
    '''Return wrapped *decorated_function* and print information when called.'''

    def wrapped(*args, **kwargs):
        '''Print information and call wrapped function with arguments.'''
        print '-' * 80
        print 'Running {0} {1}'.format(
            args[0].__class__.__name__,
            decorated_function.__name__
        )
        decorated_function(*args, **kwargs)
        print '-' * 80

    return wrapped


class PerformanceTest(object):
    '''Performance test base class.'''

    def setup(self):
        '''Setup performance test.'''

    def teardown(self):
        '''Teardown performance test.'''

    @print_test
    def profile(self):
        profiler = profile.Profile()
        profiler.enable()
        self.run()
        profiler.disable()

        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative', 'time', 'calls')
        stats.print_stats('ftrack_api|requests')

    @print_test
    def time(self):
        before = time.time()
        self.run()
        print round(time.time() - before, 3)
