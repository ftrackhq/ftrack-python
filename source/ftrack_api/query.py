# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import re
import collections

import ftrack_api.exception

LIMIT_EXPRESSION = '(?P<limit>limit \d+)'


class QueryResult(collections.Sequence):
    '''Results from a query.'''

    def __init__(self, session, expression):
        '''Initialise result set.'''
        super(QueryResult, self).__init__()
        self._session = session
        self._expression = expression
        self._results = None

    def __getitem__(self, index):
        '''Return value at *index*.'''
        if self._results is None:
            self._fetch_results()

        return self._results[index]

    def __len__(self):
        '''Return number of items.'''
        if self._results is None:
            self._fetch_results()

        return len(self._results)

    def _fetch_results(self):
        '''Fetch and store results.'''
        self._results = self._session._query(self._expression)

    def all(self):
        '''Fetch and return all data.'''
        return list(self)

    def one(self):
        '''Return exactly one single result from query.

        Raise :exc:`~ftrack_api.exception.MultipleResultsFoundError` if more
        than one result was available or
        :exc:`~ftrack_api.exception.NoResultFoundError` if no results were
        available.

        .. note::

            Both errors subclass
            :exc:`~ftrack_api.exception.IncorrectResultError` if you want to
            catch only one error type.

        '''
        if self._results:
            results = self._results
        else:
            expression = self._expression

            # See if a limit is already apply. If so temporary replace it with
            # `limit 2` and fetch results. We use `limit 2` to be able to raise
            # an exception if result contains multiple entities.
            match = re.search(LIMIT_EXPRESSION, expression)
            if match:
                value = match.groupdict().get('limit')
                expression.replace(value, 'limit 2')
            else:
                expression += ' limit 2'

            results = self._session._query(expression)

        if not results:
            raise ftrack_api.exception.NoResultFoundError()

        if len(results) != 1:
            raise ftrack_api.exception.MultipleResultsFoundError()

        return results[0]

    def first(self):
        '''Return first matching result from query.

        If no results retrieved then return None.

        '''
        # Return first item in results if results already has been fetched.
        if self._results:
            return self._results[0]

        expression = self._expression

        # See if a limit is already apply. If so temporary replace it with
        # `limit 1` and fetch results.
        match = re.search(LIMIT_EXPRESSION, expression)
        if match:
            value = match.groupdict().get('limit')
            expression.replace(value, 'limit 1')
        else:
            expression += ' limit 1'

        results = self._session._query(expression)
        if results:
            return results[0]

        return None
