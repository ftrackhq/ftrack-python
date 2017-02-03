# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

from __future__ import absolute_import

import logging
import os
import uuid
import imp
import inspect


def discover(paths, positional_arguments=None, keyword_arguments=None):
    '''Find and load plugins in search *paths*.

    Each discovered module should implement a register function that accepts
    *positional_arguments* and *keyword_arguments* as \*args and \*\*kwargs
    respectively.

    '''
    logger = logging.getLogger(__name__ + '.discover')

    if positional_arguments is None:
        positional_arguments = []

    if keyword_arguments is None:
        keyword_arguments = {}

    for path in paths:
        # Ignore empty paths that could resolve to current directory.
        path = path.strip()
        if not path:
            continue

        for base, directories, filenames in os.walk(path):
            for filename in filenames:
                name, extension = os.path.splitext(filename)
                if extension != '.py':
                    continue

                module_path = os.path.join(base, filename)
                unique_name = uuid.uuid4().hex

                try:
                    module = imp.load_source(unique_name, module_path)
                except Exception as error:
                    logger.warning(
                        'Failed to load plugin from "{0}": {1}'
                        .format(module_path, error)
                    )
                    continue

                try:
                    module.register
                except AttributeError:
                    logger.warning(
                        'Failed to load plugin that did not define a '
                        '"register" function at the module level: {0}'
                        .format(module_path)
                    )
                else:
                    register_arguments = inspect.getargspec(module.register)
                    args = register_arguments[0]
                    defaults = register_arguments[3]
                    if defaults:
                        requested_keyword_arguments = args[-len(defaults):]

                        validated_keyword_args = {
                            x: keyword_arguments[x] for x in keyword_arguments
                            if x in requested_keyword_arguments
                            }

                        if validated_keyword_args:
                            module.register(*positional_arguments,
                                            **validated_keyword_args)
                    else:
                        module.register(*positional_arguments,
                                        **keyword_arguments)
