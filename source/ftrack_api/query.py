# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import collections

import ftrack_api.exception


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
        results = self.all()
        if not results:
            raise ftrack_api.exception.NoResultFoundError()

        if len(results) != 1:
            raise ftrack_api.exception.MultipleResultsFoundError()

        return results[0]

    def first(self):
        '''Return first matching result from query.

        If no results retrieved then return None.

        '''
        # TODO: Optimise by creating a new query injecting a limit of 1 if
        # results not yet retrieved.
        results = self.all()
        if results:
            return results[0]

        return None
