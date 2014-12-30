# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import ftrack.event.expression


class Subscription(object):
    '''Represent a subscription.'''

    parser = ftrack.event.expression.Parser()

    def __init__(self, subscription):
        '''Initialise with *subscription*.'''
        self._subscription = subscription
        self._expression = self.parser.parse(subscription)

    def __str__(self):
        '''Return string representation.'''
        return self._subscription

    def includes(self, event):
        '''Return whether subscription includes *event*.'''
        return self._expression.match(event)
