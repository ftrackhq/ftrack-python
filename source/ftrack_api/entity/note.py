# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import ftrack_api.entity.base


class Note(ftrack_api.entity.base.Entity):
    '''Represent asset version.'''

    def create_reply(
        self, text, user
    ):
        '''Create a reply with *text* and *user.

        .. note::

            This is a helper method. To create replies manually use the
            standard :meth:`Session.create` method.

        '''

        return self.session.create(
            'Note', {
                'user': user,
                'text': text,
                'parent_id': self['parent_id'],
                'parent_type': self['parent_type'],
                'note_parent': self
            }
        )


class CreateNoteMixin(object):
    '''Mixin to add create_note method on entity class.'''

    def create_note(self, text, user, category=None):
        '''Create note with *text*, *user* and optional *category*.'''

        category_id = None
        if category:
            category_id = category['id']

        data = {
            'text': text,
            'user': user,
            'category_id': category_id,
            'parent_id': self['id'],
            'parent_type': self.entity_type
        }

        return self.session.create('Note', data)
