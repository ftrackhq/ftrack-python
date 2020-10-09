# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import logging
import re
import os
import ftrack_api


def get_file_type(event):
    '''return extension from the provided **file_path**.'''
    path = event['data']['file_path']

     # Get Filename.
    filename = os.path.basename(path)

    # If no extension is found return to fall back on defaut session code.
    if '.' not in filename:
        return None

    # Identify sequence searching for : %<N>d, ####, %d, min two numeral digits.
    sequence_finder_regexp = re.compile(r'((%+\d+d)|(#+)|(%d)|(\d{2,}))')

    # Result extension container.
    results = []

    # Split by dot and get the last three occurences.
    tokens = filename.split('.')[-3:]

    # Limit tokens to be taken in accoutn based on the numner of them.
    split = len(tokens) - 1 
    tokens = tokens[-split:]

    for token in tokens:
        # If any of the tokens is a sequence identifier, skip it.
        sequence_match = sequence_finder_regexp.match(token)

        if not sequence_match:
            # If is not a sequence identifier, 
            # make it part of the extension.
            results.append(token)

    # Return composed extension.
    return '.{}'.format('.'.join(results))


def register(session):
    '''Register plugin with *session*.'''
    logger = logging.getLogger('ftrack_plugin.get_file_type.register')

    # Validate that session is an instance of ftrack_api.Session. If not, assume
    # that register is being called from an old or incompatible API and return
    # without doing anything.
    if not isinstance(session, ftrack_api.Session):
        logger.debug(
            'Not subscribing plugin as passed argument {0} is not an '
            'ftrack_api.Session instance.'.format(session)
        )
        return

    session.event_hub.subscribe(
        'topic=ftrack.api.session.get-file-type-from-string',
        get_file_type
    )
