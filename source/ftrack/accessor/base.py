# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

from abc import ABCMeta, abstractmethod

from ftrack.exception import AccessorUnsupportedOperationError


class Accessor(object):
    '''Provide data access to a location.

    A location represents a specific storage, but access to that storage may
    vary. For example, both local filesystem and FTP access may be possible for
    the same storage. An accessor implements these different ways of accessing
    the same data location.

    As different accessors may access the same location, only part of a data
    path that is commonly understood may be stored in the database. The format
    of this path should be a contract between the accessors that require access
    to the same location and is left as an implementation detail. As such, this
    system provides no guarantee that two different accessors can provide access
    to the same location, though this is a clear goal. The path stored centrally
    is referred to as the **resource identifier** and should be used when
    calling any of the accessor methods that accept a *resource_identifier*
    argument.

    '''

    __metaclass__ = ABCMeta

    def __init__(self):
        '''Initialise location accessor.'''
        super(Accessor, self).__init__()

    @abstractmethod
    def list(self, resource_identifier):
        '''Return list of entries in *resource_identifier* container.

        Each entry in the returned list should be a valid resource identifier.

        Raise :py:class:`~ftrack.ftrackerror.AccessorResourceNotFoundError` if
        *resource_identifier* does not exist or
        :py:class:`~ftrack.ftrackerror.AccessorResourceInvalidError` if
        *resource_identifier* is not a container.

        '''

    @abstractmethod
    def exists(self, resource_identifier):
        '''Return if *resource_identifier* is valid and exists in location.'''

    @abstractmethod
    def is_file(self, resource_identifier):
        '''Return whether *resource_identifier* refers to a file.'''

    @abstractmethod
    def is_container(self, resource_identifier):
        '''Return whether *resource_identifier* refers to a container.'''

    @abstractmethod
    def is_sequence(self, resource_identifier):
        '''Return whether *resource_identifier* refers to a file sequence.'''

    @abstractmethod
    def open(self, resource_identifier, mode='rb'):
        '''Return :py:class:`~ftrack.Data` for *resource_identifier*.'''

    @abstractmethod
    def remove(self, resource_identifier):
        '''Remove *resource_identifier*.

        Raise :py:class:`~ftrack.ftrackerror.AccessorResourceNotFoundError` if
        *resource_identifier* does not exist.

        '''

    @abstractmethod
    def make_container(self, resource_identifier, recursive=True):
        '''Make a container at *resource_identifier*.

        If *recursive* is True, also make any intermediate containers.

        Should silently ignore existing containers and not recreate them.

        '''

    @abstractmethod
    def get_container(self, resource_identifier):
        '''Return resource_identifier of container for *resource_identifier*.

        Raise
        :py:class:`~ftrack.ftrackerror.AccessorParentResourceNotFoundError` if
        container of *resource_identifier* could not be determined.

        '''

    def remove_container(self, resource_identifier):
        '''Remove container at *resource_identifier*.'''
        return self.remove(resource_identifier)

    def get_filesystem_path(self, resource_identifier):
        '''Return filesystem path for *resource_identifier*.

        Raise AccessorFilesystemPathError if filesystem path could not be
        determined from *resource_identifier* or
        AccessorUnsupportedOperationError if retrieving filesystem paths is not
        supported by this accessor.

        '''
        raise AccessorUnsupportedOperationError(
            'get_filesystem_path', resource_identifier=resource_identifier
        )
