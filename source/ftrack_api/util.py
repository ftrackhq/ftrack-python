# :coding: utf-8
# :copyright: Copyright (c) 2020 ftrack

import threading
import ftrack_api.exception


def not_thread_safe(function_to_wrap):
    def wrapper(session, *args):
        if (
            session.thread_safe_warning and
            threading.current_thread() is not session.created_from_thread
        ):
            message = 'Called from other thread: {0}. Created from {1}'.format(
                threading.current_thread(),
                session.created_from_thread
            )
            if session.thread_safe_warning == 'warn':
                session.logger.warn(message)
            elif session.thread_safe_warning == 'raise':
                raise ftrack_api.exception.ThreadError(message)

        return function_to_wrap(session, *args)

    return wrapper


class ThreadLocalRegistry(object):

    _registry = threading.local()

    def has(self):
        return hasattr(self._registry, 'value')

    def get(self):
        return self._registry.value

    def set(self, new_session):
        self._registry.value = new_session


def session_factory(creator, registry):
    def get_scoped_session():
        if not registry.has():
            scoped_session = creator()
            registry.set(scoped_session)

        return registry.get()
    return get_scoped_session
