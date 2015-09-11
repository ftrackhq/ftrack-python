# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

from __future__ import unicode_literals

import pytest

import ftrack_api
import ftrack_api.exception


def test_index(session):
    '''Index into query result.'''
    results = session.query('User')
    assert isinstance(results[2], session.types['User'])


def test_len(session):
    '''Return count of results using len.'''
    results = session.query('User where username is jenkins')
    assert len(results) == 1


def test_all(session):
    '''Return all results using convenience method.'''
    results = session.query('User').all()
    assert isinstance(results, list)
    assert len(results)


def test_one(session):
    '''Return single result using convenience method.'''
    user = session.query('User where username is jenkins').one()
    assert user['username'] == 'jenkins'


def test_one_fails_for_no_results(session):
    '''Fail to fetch single result when no results available.'''
    with pytest.raises(ftrack_api.exception.NoResultFoundError):
        session.query('User where username is does_not_exist').one()


def test_one_fails_for_multiple_results(session):
    '''Fail to fetch single result when multiple results available.'''
    with pytest.raises(ftrack_api.exception.MultipleResultsFoundError):
        session.query('User').one()


def test_first(session):
    '''Return first result using convenience method.'''
    users = session.query('User').all()

    user = session.query('User').first()
    assert user == users[0]


def test_first_returns_none_when_no_results(session):
    '''Return None when no results available.'''
    user = session.query('User where username is does_not_exist').first()
    assert user is None

