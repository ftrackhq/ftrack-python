# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import tempfile

import pytest
import ftrack
import ftrack.accessor
import ftrack.data


class TestDiskAccessor(object):
    '''Test disk accessor.'''

    def setup_method(self, method):
        '''Setup the test.'''

    def teardown_method(self, method):
        '''Teardown the test.'''

    def test_get_filesystem_path(self):
        '''Convert paths to filesystem paths.'''
        temporary_path = tempfile.mkdtemp()
        accessor = ftrack.accessor.DiskAccessor(temporary_path)

        # Absolute paths outside of configured prefix fail.
        with pytest.raises(ftrack.exception.AccessorFilesystemPathError):
            accessor.get_filesystem_path(os.path.join('/', 'test', 'foo.txt'))

        # Absolute root path.
        assert (accessor.get_filesystem_path(temporary_path) == temporary_path)

        # Absolute path within prefix.
        assert (
            accessor.get_filesystem_path(
                os.path.join(temporary_path, 'test.txt')
            ) ==
            os.path.join(temporary_path, 'test.txt')
        )

        # Relative root path
        assert (accessor.get_filesystem_path('') == temporary_path)

        # Relative path for file at root
        assert (accessor.get_filesystem_path('test.txt') ==
                os.path.join(temporary_path, 'test.txt'))

        # Relative path for file in subdirectory
        assert (accessor.get_filesystem_path('test/foo.txt') ==
                os.path.join(temporary_path, 'test', 'foo.txt'))

        # Relative path non-collapsed
        assert (accessor.get_filesystem_path('test/../foo.txt') ==
                os.path.join(temporary_path, 'foo.txt'))

        # Relative directory path without trailing slash
        assert (accessor.get_filesystem_path('test') ==
                os.path.join(temporary_path, 'test'))

        # Relative directory path with trailing slash
        assert (accessor.get_filesystem_path('test/') ==
                os.path.join(temporary_path, 'test'))

    def test_list(self):
        '''List entries.'''
        temporary_path = tempfile.mkdtemp()
        accessor = ftrack.accessor.DiskAccessor(temporary_path)

        # File in root directory
        assert (accessor.list('') == [])
        data = accessor.open('test.txt', 'w+')
        data.close()
        assert (accessor.list('') == ['test.txt'])

        # File in subdirectory
        accessor.make_container('test_dir')
        assert (accessor.list('test_dir') == [])
        data = accessor.open('test_dir/test.txt', 'w+')
        data.close()

        listing = accessor.list('test_dir')
        assert (listing == ['test_dir/test.txt'])

        # Is a valid resource
        assert (accessor.exists(listing[0]) is True)

    def test_exists(self):
        '''Check whether path exists.'''
        temporary_path = tempfile.mkdtemp()
        accessor = ftrack.accessor.DiskAccessor(temporary_path)

        _, temporary_file = tempfile.mkstemp(dir=temporary_path)
        assert (accessor.exists(temporary_file) is True)

        # Missing path
        assert (accessor.exists('non-existant.txt') is False)

    def test_is_file(self):
        '''Check whether path is a file.'''
        temporary_path = tempfile.mkdtemp()
        accessor = ftrack.accessor.DiskAccessor(temporary_path)

        _, temporary_file = tempfile.mkstemp(dir=temporary_path)
        assert (accessor.is_file(temporary_file) is True)

        # Missing path
        assert (accessor.is_file('non-existant.txt') is False)

        # Directory
        temporary_directory = tempfile.mkdtemp(dir=temporary_path)
        assert (accessor.is_file(temporary_directory) is False)

    def test_is_container(self):
        '''Check whether path is a container.'''
        temporary_path = tempfile.mkdtemp()
        accessor = ftrack.accessor.DiskAccessor(temporary_path)

        temporary_directory = tempfile.mkdtemp(dir=temporary_path)
        assert (accessor.is_container(temporary_directory) is True)

        # Missing path
        assert (accessor.is_container('non-existant') is False)

        # File
        _, temporary_file = tempfile.mkstemp(dir=temporary_path)
        assert (accessor.is_container(temporary_file) is False)

    def test_is_sequence(self):
        '''Check whether path is a sequence.'''
        temporary_path = tempfile.mkdtemp()
        accessor = ftrack.accessor.DiskAccessor(temporary_path)

        with pytest.raises(ftrack.exception.AccessorUnsupportedOperationError):
            accessor.is_sequence('foo.%04d.exr')

    def test_open(self):
        '''Open file.'''
        temporary_path = tempfile.mkdtemp()
        accessor = ftrack.accessor.DiskAccessor(temporary_path)

        with pytest.raises(ftrack.exception.AccessorResourceNotFoundError):
            accessor.open('test.txt', 'r')

        data = accessor.open('test.txt', 'w+')
        assert (isinstance(data, ftrack.data.Data) is True)
        assert (data.read() == '')
        data.write('test data')
        data.close()

        data = accessor.open('test.txt', 'r')
        assert (data.read() == 'test data')
        data.close()

    def test_remove(self):
        '''Delete path.'''
        temporary_path = tempfile.mkdtemp()
        accessor = ftrack.accessor.DiskAccessor(temporary_path)

        _, temporary_file = tempfile.mkstemp(dir=temporary_path)
        accessor.remove(temporary_file)
        assert (os.path.exists(temporary_file) is False)

        temporary_directory = tempfile.mkdtemp(dir=temporary_path)
        accessor.remove(temporary_directory)
        assert (os.path.exists(temporary_directory) is False)

    def test_make_container(self):
        '''Create container.'''
        temporary_path = tempfile.mkdtemp()
        accessor = ftrack.accessor.DiskAccessor(temporary_path)

        accessor.make_container('test')
        assert (os.path.isdir(os.path.join(temporary_path, 'test')) is True)

        # Recursive
        accessor.make_container('test/a/b/c')
        assert (
            os.path.isdir(
                os.path.join(temporary_path, 'test', 'a', 'b', 'c')
            ) is
            True
        )

        # Non-recursive fail
        with pytest.raises(
            ftrack.exception.AccessorParentResourceNotFoundError
        ):
            accessor.make_container('test/d/e/f', recursive=False)

        # Existing succeeds
        accessor.make_container('test/a/b/c')

    def test_get_container(self):
        '''Get container from resource_identifier.'''
        # With prefix.
        temporary_path = tempfile.mkdtemp()
        accessor = ftrack.accessor.DiskAccessor(prefix=temporary_path)

        assert (
            accessor.get_container(os.path.join('test', 'a')) ==
            'test'
        )

        assert (
            accessor.get_container(os.path.join('test', 'a/')) ==
            'test'
        )

        assert (
            accessor.get_container('test') ==
            ''
        )

        with pytest.raises(
            ftrack.exception.AccessorParentResourceNotFoundError
        ):
            accessor.get_container('')

        with pytest.raises(
            ftrack.exception.AccessorParentResourceNotFoundError
        ):
            accessor.get_container(temporary_path)

        # Without prefix.
        accessor = ftrack.accessor.DiskAccessor(prefix='')

        assert (
            accessor.get_container(os.path.join(temporary_path, 'test', 'a')) ==
            os.path.join(temporary_path, 'test')
        )

        assert (
            accessor.get_container(
                os.path.join(temporary_path, 'test', 'a/')
            ) ==
            os.path.join(temporary_path, 'test')
        )

        assert (
            accessor.get_container(os.path.join(temporary_path, 'test')) ==
            temporary_path
        )
