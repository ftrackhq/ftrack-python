# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import re
import collections

import ftrack_api.exception


class QueryResult(collections.Sequence):
    '''Results from a query.'''

    OFFSET_EXPRESSION = re.compile('(?P<offset>offset (?P<value>\d+))')
    LIMIT_EXPRESSION = re.compile('(?P<limit>limit (?P<value>\d+))')

    def __init__(self, session, expression, page_size=500):
        '''Initialise result set.

        *session* should be an instance of :class:`ftrack_api.session.Session`
        that will be used for executing the query *expression*.

        *page_size* should be an integer specifying the maximum number of
        records to fetch in one request allowing the results to be fetched
        incrementally in a transparent manner for optimal performance. The page
        size will override any limit present in the expression, but any
        embedded offset and limit will still be honoured in terms of the overall
        result.

        .. warning::

            Setting *page_size* to a very large amount may negatively impact
            performance of not only the caller, but the server in general.

        '''
        super(QueryResult, self).__init__()
        self._session = session
        self._results = []

        (
            self._expression,
            self._offset,
            self._limit
        ) = self._extract_offset_and_limit(expression)

        self._page_size = page_size
        self._next_offset = self._offset

    def _extract_offset_and_limit(self, expression):
        '''Process *expression* extracting offset and limit.

        Return (expression, offset, limit).

        '''
        offset = 0
        match = self.OFFSET_EXPRESSION.search(expression)
        if match:
            offset = int(match.group('value'))
            expression = (
                expression[:match.start('offset')] +
                expression[match.end('offset'):]
            )

        limit = None
        match = self.LIMIT_EXPRESSION.search(expression)
        if match:
            limit = int(match.group('value'))
            expression = (
                expression[:match.start('limit')] +
                expression[match.end('limit'):]
            )

        return expression, offset, limit

    def __getitem__(self, index):
        '''Return value at *index*.'''
        while self._can_fetch_more() and index < len(self._results):
            self._fetch_more()

        return self._results[index]

    def __len__(self):
        '''Return number of items.'''
        while self._can_fetch_more():
            self._fetch_more()

        return len(self._results)

    def _can_fetch_more(self):
        '''Return whether more results are available to fetch.'''
        return self._next_offset is not None

    def _fetch_more(self):
        '''Fetch next page of results if available.'''
        if not self._can_fetch_more():
            return

        expression = '{0} offset {1} limit {2}'.format(
            self._expression, self._next_offset, self._page_size
        )
        records, metadata = self._session._query(expression)
        self._results.extend(records)

        self._next_offset = metadata.get('next', {}).get('offset', None)

    def all(self):
        '''Fetch and return all data.'''
        return list(self)

    def one(self):
        '''Return exactly one single result from query by applying a limit.

        Raise :exc:`ValueError` if an existing limit is already present in the
        expression.

        Raise :exc:`~ftrack_api.exception.MultipleResultsFoundError` if more
        than one result was available or
        :exc:`~ftrack_api.exception.NoResultFoundError` if no results were
        available.

        .. note::

            Both errors subclass
            :exc:`~ftrack_api.exception.IncorrectResultError` if you want to
            catch only one error type.

        '''
        expression = self._expression

        if self.LIMIT_EXPRESSION.search(expression):
            raise ValueError(
                'Expression already contains a limit clause.'
            )

        # Apply custom limit as optimisation. A limit of 2 is used rather than
        # 1 so that it is possible to test for multiple matching entries
        # case.
        expression += ' limit 2'

        results = self._session._query(expression)

        if not results:
            raise ftrack_api.exception.NoResultFoundError()

        if len(results) != 1:
            raise ftrack_api.exception.MultipleResultsFoundError()

        return results[0]

    def first(self):
        '''Return first matching result from query by applying a limit.

        Raise :exc:`ValueError` if an existing limit is already present in the
        expression.

        If no matching result available return None.

        '''
        expression = self._expression

        if self.LIMIT_EXPRESSION.search(expression):
            raise ValueError(
                'Expression already contains a limit clause.'
            )

        # Apply custom limit as optimisation.
        expression += ' limit 1'

        results = self._session._query(expression)

        if results:
            return results[0]

        return None
