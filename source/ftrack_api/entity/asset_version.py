# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import ftrack_api.entity.base


class AssetVersion(ftrack_api.entity.base.Entity):
    '''Represent asset version.'''

    def create_component(
        self, path, data=None, location=None
    ):
        '''Create a new component from *path* with additional *data*

        .. note::

            This is a helper method. To create components manually use the
            standard :meth:`Session.create` method.

        *path* can be a string representing a filesystem path to the data to
        use for the component. The *path* can also be specified as a sequence
        string, in which case a sequence component with child components for
        each item in the sequence will be created automatically. The accepted
        format for a sequence is '{head}{padding}{tail} [{ranges}]'. For
        example::

            '/path/to/file.%04d.ext [1-5, 7, 8, 10-20]'

        .. seealso::

            `Clique documentation <http://clique.readthedocs.org>`_

        *data* should be a dictionary of any additional data to construct the
        component with (as passed to :meth:`Session.create`). This version is
        automatically set as the component's version.

        If *location* is specified then automatically add component to that
        location.

        '''
        if data is None:
            data = {}

        data.pop('version_id', None)
        data['version'] = self

        return self.session.create_component(path, data=data, location=location)
