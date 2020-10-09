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
