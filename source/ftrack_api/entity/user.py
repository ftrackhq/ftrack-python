# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import arrow

import ftrack_api.entity.base
import ftrack_api.exception


class User(ftrack_api.entity.base.Entity):
    '''Represent a user.'''

    def start_timer(self, context=None, comment='', name=None, force=False):
        '''Start a timer for *context* and return it.

        *force* can be used to automatically stop an existing timer and create a
        timelog for it. If you need to get access to the created timelog, use
        :func:`stop_timer` instead.

        *comment* and *name* are optional but will be set on the timer.

        .. note::

            This method will automatically commit the changes and if *force* is
            False then it will fail with a
            :class:`ftrack_api.exception.NotUniqueError` exception if a
            timer is already running.

        '''
        if force:
            try:
                self.stop_timer()
            except ftrack_api.exception.NoResultFoundError:
                self.logger.debug('Failed to stop existing timer.')

        timer = self.session.create('Timer', {
            'user': self,
            'context': context
        })

        # Commit the new timer and try to catch any error that indicate another
        # timelog already exists and inform the user about it.
        try:
            self.session.commit()
        except ftrack_api.exception.ServerError as error:
            if 'IntegrityError' in str(error):
                raise ftrack_api.exception.NotUniqueError(
                    ('Failed to start a timelog for user with id: {0}, it is '
                     'likely that a timer is already running. Either use '
                     'force=True or stop the timer first.').format(self['id'])
                )
            else:
                # Reraise the error as it might be something unrelated.
                raise

        return timer

    def stop_timer(self):
        '''Stop the current timer and return a timelog created from it.

        If a timer is not running, a
        :exc:`ftrack_api.exception.NoResultFoundError` exception will be
        raised.

        .. note::

            This method will automatically commit the changes.

        '''
        timer = self.session.query(
            'Timer where user_id = "{0}"'.format(self['id'])
        ).one()

        delta = arrow.now() - timer['start']
        duration = delta.days * 24 * 60 * 60 + delta.seconds

        timelog = self.session.create('Timelog', {
            'user_id': timer['user_id'],
            'context_id': timer['context_id'],
            'comment': timer['comment'],
            'start': timer['start'],
            'duration': duration,
            'name': timer['name']
        })

        self.session.delete(timer)
        self.session.commit()

        return timelog
