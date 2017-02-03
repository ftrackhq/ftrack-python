# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import textwrap
import logging
import uuid

import pytest

import ftrack_api.plugin


@pytest.fixture()
def valid_plugin(temporary_path):
    '''Return path to directory containing a valid plugin.'''
    with open(os.path.join(temporary_path, 'plugin.py'), 'w') as file_object:
        file_object.write(textwrap.dedent('''
            def register(*args, **kw):
                print "Registered", args, kw
        '''))

    return temporary_path


@pytest.fixture()
def python_non_plugin(temporary_path):
    '''Return path to directory containing Python file that is non plugin.'''
    with open(os.path.join(temporary_path, 'non.py'), 'w') as file_object:
        file_object.write(textwrap.dedent('''
            print "Not a plugin"

            def not_called():
                print "Not called"
        '''))

    return temporary_path


@pytest.fixture()
def non_plugin(temporary_path):
    '''Return path to directory containing file that is non plugin.'''
    with open(os.path.join(temporary_path, 'non.txt'), 'w') as file_object:
        file_object.write('Never seen')

    return temporary_path


@pytest.fixture()
def broken_plugin(temporary_path):
    '''Return path to directory containing broken plugin.'''
    with open(os.path.join(temporary_path, 'broken.py'), 'w') as file_object:
        file_object.write('syntax error')

    return temporary_path


def test_discover_empty_paths(capsys):
    '''Discover no plugins when paths are empty.'''
    ftrack_api.plugin.discover(['   '])
    output, error = capsys.readouterr()
    assert not output
    assert not error


def test_discover_valid_plugin(valid_plugin, capsys):
    '''Discover valid plugin.'''
    ftrack_api.plugin.discover([valid_plugin], (1, 2), {'3': 4})
    output, error = capsys.readouterr()
    assert 'Registered (1, 2) {\'3\': 4}' in output


def test_discover_python_non_plugin(python_non_plugin, capsys):
    '''Discover Python non plugin.'''
    ftrack_api.plugin.discover([python_non_plugin])
    output, error = capsys.readouterr()
    assert 'Not a plugin' in output
    assert 'Not called' not in output


def test_discover_non_plugin(non_plugin, capsys):
    '''Discover non plugin.'''
    ftrack_api.plugin.discover([non_plugin])
    output, error = capsys.readouterr()
    assert not output
    assert not error


def test_discover_broken_plugin(broken_plugin, caplog):
    '''Discover broken plugin.'''
    ftrack_api.plugin.discover([broken_plugin])

    records = caplog.records()
    assert len(records) == 1
    assert records[0].levelno is logging.WARNING
    assert 'Failed to load plugin' in records[0].message


@pytest.fixture()
def valid_plugin_with_keywords(temporary_path):
    '''Return path to directory containing a valid plugin.'''
    with open(os.path.join(temporary_path, 'plugin.py'), 'w') as file_object:
        file_object.write(textwrap.dedent('''
            def register(*args, plugin_arguments=None):
                print "Registered with plugin_arguments", args, plugin_arguments
        '''))

    return temporary_path


def test_discover_valid_plugin_with_keywords(valid_plugin_with_keywords,
                                             capsys):
    '''Discover valid plugin that uses plugin arguments.'''
    huddle_id = uuid.uuid4().hex
    ftrack_api.plugin.discover(
        [valid_plugin_with_keywords],
        (1, 2),
        keyword_arguments={"plugin_arguments": {'huddle': huddle_id}}
    )
    output, error = capsys.readouterr()
    register_message = ("Registered with plugin_arguments (1, 2) "
                        "{\'huddle\': {0}}".format(huddle_id))
    # register_message = "Registered with plugin_arguments (1, 2)"
    assert register_message in output
