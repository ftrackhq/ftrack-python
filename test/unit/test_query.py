# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack


def test_index(session):
    '''Index into query result.'''
    results = session.query('User')
    assert isinstance(results[2], session.types['User'])


def test_len(session):
    '''Return count of results using len.'''
    results = session.query('User where username is jenkins')
    assert len(results) == 1
