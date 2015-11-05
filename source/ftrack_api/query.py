# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import re
import collections

import ftrack_api.exception


class QueryResult(collections.Sequence):
    '''Results from a query.'''

    LIMIT_EXPRESSION = re.compile('(?P<limit> limit \d+)')

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

        This method applies a new limit temporarily overriding any existing
        limit in the expression. Therefore it is safe to call this method
        without affecting the behaviour of other methods like :meth:`first`.

        '''
        if self._results is not None:
            results = self._results
        else:
            expression = self._expression

            # Apply custom limit as optimisation, temporarily replacing any
            # existing limit in the expression. A limit of 2 is used rather than
            # 1 so that it is possible to test for multiple matching entries
            # case.
            limiter = ' limit 2'
            expression, matched = re.subn(
                self.LIMIT_EXPRESSION, limiter, expression
            )
            if not matched:
                expression += limiter

            results = self._session._query(expression)

        if not results:
            raise ftrack_api.exception.NoResultFoundError()

        if len(results) != 1:
            raise ftrack_api.exception.MultipleResultsFoundError()

        return results[0]

    def first(self):
        '''Return first matching result from query.

        This method applies a new limit temporarily overriding any existing
        limit in the expression. Therefore it is safe to call this method
        without affecting the behaviour of other methods like :meth:`all`::

            query = session.query(
                'Task where status.name is "In Progress" limit 10'
            )
            query.first()  # Return first task in progress
            query.all()  # Return first 10 matching tasks

        If no matching result available return None.

        '''
        # Return first item in results if results already has been fetched.
        if self._results:
            return self._results[0]

        expression = self._expression

        # Apply custom limit as optimisation, temporarily replacing any
        # existing limit in the expression.
        limiter = ' limit 1'
        expression, matched = re.subn(
            self.LIMIT_EXPRESSION, limiter, expression
        )
        if not matched:
            expression += limiter

        results = self._session._query(expression)
        if results:
            return results[0]

        return None
