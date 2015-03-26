# :coding: utf-8
# :copyright: Copyright (c) 2013 ftrack

import os
from abc import ABCMeta, abstractmethod
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class Data(object):
    '''File-like object for manipulating data.'''

    __metaclass__ = ABCMeta

    def __init__(self):
        '''Initialise data access.'''
        self.closed = False

    def __del__(self):
        '''Perform cleanup on object deletion.'''
        self.close()

    @abstractmethod
    def read(self, limit=None):
        '''Return content from current position up to *limit*.'''

    @abstractmethod
    def write(self, content):
        '''Write content at current position.'''

    def flush(self):
        '''Flush buffers ensuring data written.'''

    def seek(self, offset, whence=os.SEEK_SET):
        '''Move internal pointer by *offset*.

        The *whence* argument is optional and defaults to os.SEEK_SET or 0
        (absolute file positioning); other values are os.SEEK_CUR or 1
        (seek relative to the current position) and os.SEEK_END or 2
        (seek relative to the file's end).

        '''
        raise NotImplementedError('Seek not supported.')

    def tell(self):
        '''Return current position of internal pointer.'''
        raise NotImplementedError('Tell not supported.')

    def close(self):
        '''Flush buffers and prevent further access.'''
        self.flush()
        self.closed = True


class FileWrapper(Data):
    '''Data wrapper for Python file objects.'''

    def __init__(self, wrapped_file):
        '''Initialise access to *wrapped_file*.'''
        self.wrapped_file = wrapped_file
        super(FileWrapper, self).__init__()

    def read(self, limit=None):
        '''Return content from current position up to *limit*.'''
        if limit is None:
            limit = -1

        return self.wrapped_file.read(limit)

    def write(self, content):
        '''Write content at current position.'''
        self.wrapped_file.write(content)

    def flush(self):
        '''Flush buffers ensuring data written.'''
        super(FileWrapper, self).flush()
        if hasattr(self.wrapped_file, 'flush'):
            self.wrapped_file.flush()

    def seek(self, offset, whence=os.SEEK_SET):
        '''Move internal pointer by *offset*.'''
        self.wrapped_file.seek(offset, whence)

    def tell(self):
        '''Return current position of internal pointer.'''
        return self.wrapped_file.tell()

    def close(self):
        '''Flush buffers and prevent further access.'''
        if not self.closed:
            super(FileWrapper, self).close()
            if hasattr(self.wrapped_file, 'close'):
                self.wrapped_file.close()


class File(FileWrapper):
    '''Data wrapper accepting filepath.'''

    def __init__(self, path, mode='rb'):
        '''Open file at *path* with *mode*.'''
        file_object = open(path, mode)
        super(File, self).__init__(file_object)


class String(FileWrapper):
    '''Data wrapper using StringIO instance.'''

    def __init__(self, content=None):
        '''Initialise data with *content*.'''
        super(String, self).__init__(StringIO())

        if content is not None:
            self.wrapped_file.write(content)
            self.wrapped_file.seek(0)
