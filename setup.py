# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import os

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

from pkg_resources import get_distribution, DistributionNotFound


ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
RESOURCE_PATH = os.path.join(ROOT_PATH, 'resource')
SOURCE_PATH = os.path.join(ROOT_PATH, 'source')
README_PATH = os.path.join(ROOT_PATH, 'README.rst')

try:
    release = get_distribution('ftrack-python-api').version
    # take major/minor/patch
    VERSION = '.'.join(release.split('.')[:3])
except DistributionNotFound:
     # package is not installed
    VERSION = 'Unknown version'

# Custom commands.
class PyTest(TestCommand):
    '''Pytest command.'''

    def finalize_options(self):
        '''Finalize options to be used.'''
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        '''Import pytest and run.'''
        import pytest
        raise SystemExit(pytest.main(self.test_args))


version_template = '''
# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

__version__ = {version!r}
'''


# Call main setup.
setup(
    name='ftrack-python-api',
    description='Python API for ftrack.',
    long_description=open(README_PATH).read(),
    keywords='ftrack, python, api, sdk',
    url='https://github.com/ftrackhq/ftrack-python',
    author='ftrack',
    author_email='support@ftrack.com',
    license='Apache License (2.0)',
    packages=find_packages(SOURCE_PATH),
    project_urls={
        "Documentation": "http://ftrack-python-api.rtd.ftrack.com/en/{}/".format(VERSION),
        "Source Code": "https://github.com/ftrackhq/ftrack-python/src/{}".format(VERSION),
    },
    package_dir={
        '': 'source'
    },
    use_scm_version={
        'write_to': 'source/ftrack_api/_version.py',
        'write_to_template': version_template,
    },
    setup_requires=[
        'sphinx >= 1.2.2, < 1.6',
        'sphinx_rtd_theme >= 0.1.6, < 1',
        'lowdown >= 0.1.0, < 2',
        'setuptools>=30.3.0',
        'setuptools_scm'
    ],
    install_requires=[
        'requests >= 2, <3',
        'arrow >= 0.4.4, < 1',
        'termcolor >= 1.1.0, < 2',
        'pyparsing >= 2.0, < 3',
        'clique == 1.6.1',
        'websocket-client >= 0.40.0, < 1',
        'future >=0.16.0, < 1',
        'six >= 1.13.0, < 2',
        'appdirs >=1, <2'
    ],
    tests_require=[
        'pytest >= 4.6',
        'pytest-mock',
        'mock',
        'flaky'
    ],
    cmdclass={
        'test': PyTest
    },
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9'

    ],
    zip_safe=False,
    python_requires=">=2.7.9, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, !=3.5.*, < 3.10"
)
