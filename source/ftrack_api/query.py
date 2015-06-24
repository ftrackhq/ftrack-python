# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import collections


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
