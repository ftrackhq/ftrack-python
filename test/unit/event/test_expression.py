# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import operator
import inspect

import pytest

from ftrack_api.event.expression import (
    Expression, All, Any, Not, Condition, Parser
)
from ftrack_api.exception import ParseError


@pytest.fixture()
def candidate():
    '''Return common candidate to test expressions against.'''
    return {
        'id': 10,
        'name': 'value',
        'change': {
            'name': 'value',
            'new_value': 10
        }
    }


@pytest.mark.parametrize('expression, expected', [
    pytest.param('', Expression(), marks=pytest.mark.xfail, id='Empty Expression'),
    pytest.param('invalid', ParseError, id='Invalid Expression'),
    pytest.param('key=value nor other=value', ParseError, id='Invalid Conjunction'),
    pytest.param('key=value', Condition('key', operator.eq, 'value'), id='Basic Condition'),
    pytest.param('key="value"', Condition('key', operator.eq, 'value'), id='Basic Quoted Condition'),
    pytest.param(
        'a=b and ((c=d or e!=f) and not g.h > 10)',
        All([
            Condition('a', operator.eq, 'b'),
            All([
                Any([
                    Condition('c', operator.eq, 'd'),
                    Condition('e', operator.ne, 'f')
                ]),
                Not(
                    Condition('g.h', operator.gt, 10)
                )
            ])
        ]),
        id='Complex Condition'
    )
])
def test_parser_parse(expression, expected):
    '''Parse expression into Expression instances.'''
    parser = Parser()

    if inspect.isclass(expected) and issubclass(expected, Exception):
        with pytest.raises(expected):
            parser.parse(expression)
    else:
        assert str(parser.parse(expression)) == str(expected)


@pytest.mark.parametrize('expression, expected', [
    pytest.param(Expression(), '<Expression>', id='Expressions'),
    pytest.param(All([Expression(), Expression()]), '<All [<Expression> <Expression>]>', id='All'),
    pytest.param(Any([Expression(), Expression()]), '<Any [<Expression> <Expression>]>', id='Any'),
    pytest.param(Not(Expression()), '<Not <Expression>>', id='Not'),
    pytest.param(Condition('key', '=', 'value'), '<Condition key=value>', id='Condition')
])
def test_string_representation(expression, expected):
    '''String representation of expression.'''
    assert str(expression) == expected


@pytest.mark.parametrize('expression, expected', [
    # Expression
    pytest.param(Expression(), True, id='Expression-always matches'),

    # All
    pytest.param(All(), True, id='All-no expressions always matches'),
    pytest.param(All([Expression(), Expression()]), True, id='All-all match'),
    pytest.param(All([Expression(), Condition('test', operator.eq, 'value')]), False, id='All-not all match'),

    # Any
    pytest.param(Any(), False, id='Any-no expressions never matches'),
    pytest.param(Any([Expression(), Condition('test', operator.eq, 'value')]), True, id='Any-some match'),
    pytest.param(Any([
        Condition('test', operator.eq, 'value'),
        Condition('other', operator.eq, 'value')
    ]), False, id='Any-none match'),

    # Not
    pytest.param(Not(Expression()), False, id='Not-invert positive match'),
    pytest.param(Not(Not(Expression())), True, id='Not-double negative is positive match')
])
def test_match(expression, candidate, expected):
    '''Determine if candidate matches expression.'''
    assert expression.match(candidate) is expected


def parametrize_test_condition_match(metafunc):
    '''Parametrize condition_match tests.'''
    identifiers = []
    data = []

    matrix = {
        # Operator, match, no match
        operator.eq: {
            'match': 10, 'no-match': 20,
            'wildcard-match': 'valu*', 'wildcard-no-match': 'values*'
        },
        operator.ne: {'match': 20, 'no-match': 10},
        operator.ge: {'match': 10, 'no-match': 20},
        operator.le: {'match': 10, 'no-match': 0},
        operator.gt: {'match': 0, 'no-match': 10},
        operator.lt: {'match': 20, 'no-match': 10}
    }

    for operator_function, values in matrix.items():
        for value_label, value in values.items():
            if value_label.startswith('wildcard'):
                key_options = {
                    'plain': 'name',
                    'nested': 'change.name'
                }
            else:
                key_options = {
                    'plain': 'id',
                    'nested': 'change.new_value'
                }

            for key_label, key in key_options.items():
                identifier = '{} operator {} key {}'.format(
                    operator_function.__name__, key_label, value_label
                )

                data.append(pytest.param(
                    key, operator_function, value,
                    'no-match' not in value_label, id=identifier
                ))

    metafunc.parametrize(
        'key, operator, value, expected', data
    )


def test_condition_match(key, operator, value, candidate, expected):
    '''Determine if candidate matches condition expression.'''
    condition = Condition(key, operator, value)
    assert condition.match(candidate) is expected
