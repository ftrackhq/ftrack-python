# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import tempfile
import functools
import uuid
import textwrap
import datetime
import json

import pytest
import mock
import arrow

import ftrack_api
import ftrack_api.cache
import ftrack_api.inspection
import ftrack_api.symbol
import ftrack_api.exception


@pytest.fixture(params=['memory', 'persisted'])
def cache(request):
    '''Return cache.'''
    if request.param == 'memory':
        cache = None  # There is already a default Memory cache present.
    elif request.param == 'persisted':
        cache_path = os.path.join(
            tempfile.gettempdir(), '{0}.dbm'.format(uuid.uuid4().hex)
        )

        cache = lambda session: ftrack_api.cache.SerialisedCache(
            ftrack_api.cache.FileCache(cache_path),
            encode=functools.partial(
                session.encode, entity_attribute_strategy='persisted_only'
            ),
            decode=session.decode
        )

        def cleanup():
            '''Cleanup.'''
            try:
                os.remove(cache_path)
            except OSError:
                # BSD DB (Mac OSX) implementation of the interface will append
                # a .db extension.
                os.remove(cache_path + '.db')

        request.addfinalizer(cleanup)

    return cache


@pytest.fixture()
def temporary_invalid_schema_cache(request):
    '''Return schema cache path to invalid schema cache file.'''
    schema_cache_path = os.path.join(
        tempfile.gettempdir(),
        'ftrack_api_schema_cache_test_{0}.json'.format(uuid.uuid4().hex)
    )

    with open(schema_cache_path, 'w') as file_:
        file_.write('${invalid json}')

    def cleanup():
        '''Cleanup.'''
        os.remove(schema_cache_path)

    request.addfinalizer(cleanup)

    return schema_cache_path


@pytest.fixture()
def temporary_valid_schema_cache(request, mocked_schemas):
    '''Return schema cache path to valid schema cache file.'''
    schema_cache_path = os.path.join(
        tempfile.gettempdir(),
        'ftrack_api_schema_cache_test_{0}.json'.format(uuid.uuid4().hex)
    )

    with open(schema_cache_path, 'w') as file_:
        json.dump(mocked_schemas, file_, indent=4)

    def cleanup():
        '''Cleanup.'''
        os.remove(schema_cache_path)

    request.addfinalizer(cleanup)

    return schema_cache_path


def test_get_entity(session, user):
    '''Retrieve an entity by type and id.'''
    matching = session.get(*ftrack_api.inspection.identity(user))
    assert matching == user


def test_get_non_existant_entity(session):
    '''Retrieve a non-existant entity by type and id.'''
    matching = session.get('User', 'non-existant-id')
    assert matching is None


def test_get_entity_of_invalid_type(session):
    '''Fail to retrieve an entity using an invalid type.'''
    with pytest.raises(KeyError):
        session.get('InvalidType', 'id')


def test_create(session):
    '''Create entity.'''
    user = session.create('User', {'username': 'martin'})
    with session.auto_populating(False):
        assert user['id'] is not ftrack_api.symbol.NOT_SET
        assert user['username'] == 'martin'
        assert user['email'] is ftrack_api.symbol.NOT_SET


def test_create_using_only_defaults(session):
    '''Create entity using defaults only.'''
    user = session.create('User')
    with session.auto_populating(False):
        assert user['id'] is not ftrack_api.symbol.NOT_SET
        assert user['username'] is ftrack_api.symbol.NOT_SET


def test_create_using_server_side_defaults(session):
    '''Create entity using server side defaults.'''
    user = session.create('User')
    with session.auto_populating(False):
        assert user['id'] is not ftrack_api.symbol.NOT_SET
        assert user['username'] is ftrack_api.symbol.NOT_SET

    session.commit()
    assert user['username'] is not ftrack_api.symbol.NOT_SET


def test_create_overriding_defaults(session):
    '''Create entity overriding defaults.'''
    uid = str(uuid.uuid4())
    user = session.create('User', {'id': uid})
    with session.auto_populating(False):
        assert user['id'] == uid


def test_create_with_reference(session):
    '''Create entity with a reference to another.'''
    status = session.query('Status')[0]
    task = session.create('Task', {'status': status})
    assert task['status'] is status


def test_ensure_new_entity(session, unique_name):
    '''Ensure entity, creating first.'''
    entity = session.ensure('User', {'username': unique_name})
    assert entity['username'] == unique_name


def test_ensure_entity_with_non_string_data_types(session):
    '''Ensure entity against non-string data types, creating first.'''
    datetime = arrow.get()
    first = session.ensure('Timelog', {'start': datetime, 'duration': 10})

    with mock.patch.object(session, 'create') as mocked:
        session.ensure('Timelog', {'start': datetime, 'duration': 10})
        assert not mocked.called

    assert first['start'] == datetime
    assert first['duration'] == 10


def test_ensure_entity_with_identifying_keys(session, unique_name):
    '''Ensure entity, checking using keys subset and then creating.'''
    entity = session.ensure(
        'User', {'username': unique_name, 'email': 'test@example.com'},
        identifying_keys=['username']
    )
    assert entity['username'] == unique_name


def test_ensure_entity_with_invalid_identifying_keys(session, unique_name):
    '''Fail to ensure entity when identifying key missing from data.'''
    with pytest.raises(KeyError):
        session.ensure(
            'User', {'username': unique_name, 'email': 'test@example.com'},
            identifying_keys=['invalid']
        )


def test_ensure_entity_with_missing_identifying_keys(session):
    '''Fail to ensure entity when no identifying keys determined.'''
    with pytest.raises(ValueError):
        session.ensure('User', {})


def test_ensure_existing_entity(session, unique_name):
    '''Ensure existing entity.'''
    entity = session.ensure('User', {'first_name': unique_name})

    # Second call should not commit any new entity, just retrieve the existing.
    with mock.patch.object(session, 'create') as mocked:
        retrieved = session.ensure('User', {'first_name': unique_name})
        assert not mocked.called
        assert retrieved == entity


def test_ensure_update_existing_entity(session, unique_name):
    '''Ensure and update existing entity.'''
    entity = session.ensure(
        'User', {'first_name': unique_name, 'email': 'anon@example.com'}
    )
    assert entity['email'] == 'anon@example.com'

    # Second call should commit updates.
    retrieved = session.ensure(
        'User', {'first_name': unique_name, 'email': 'test@example.com'},
        identifying_keys=['first_name']
    )
    assert retrieved == entity
    assert retrieved['email'] == 'test@example.com'


def test_reconstruct_entity(session):
    '''Reconstruct entity.'''
    uid = str(uuid.uuid4())
    data = {
        'id': uid,
        'username': 'martin',
        'email': 'martin@example.com'
    }
    user = session.create('User', data, reconstructing=True)

    for attribute in user.attributes:
        # No local attributes should be set.
        assert attribute.get_local_value(user) is ftrack_api.symbol.NOT_SET

        # Only remote attributes that had explicit values should be set.
        value = attribute.get_remote_value(user)
        if attribute.name in data:
            assert value == data[attribute.name]
        else:
            assert value is ftrack_api.symbol.NOT_SET


def test_reconstruct_entity_does_not_apply_defaults(session):
    '''Reconstruct entity does not apply defaults.'''
    # Note: Use private method to avoid merge which requires id be set.
    user = session._create('User', {}, reconstructing=True)
    with session.auto_populating(False):
        assert user['id'] is ftrack_api.symbol.NOT_SET


def test_reconstruct_empty_entity(session):
    '''Reconstruct empty entity.'''
    # Note: Use private method to avoid merge which requires id be set.
    user = session._create('User', {}, reconstructing=True)

    for attribute in user.attributes:
        # No local attributes should be set.
        assert attribute.get_local_value(user) is ftrack_api.symbol.NOT_SET

        # No remote attributes should be set.
        assert attribute.get_remote_value(user) is ftrack_api.symbol.NOT_SET


def test_delete_operation_ordering(session, unique_name):
    '''Delete entities in valid order.'''
    # Construct entities.
    project_schema = session.query('ProjectSchema').first()
    project = session.create('Project', {
        'name': unique_name,
        'full_name': unique_name,
        'project_schema': project_schema
    })

    sequence = session.create('Sequence', {
        'name': unique_name,
        'parent': project
    })

    session.commit()

    # Delete in order that should succeed.
    session.delete(sequence)
    session.delete(project)

    session.commit()


def test_create_then_delete_operation_ordering(session, unique_name):
    '''Create and delete entity in one transaction.'''
    entity = session.create('User', {'username': unique_name})
    session.delete(entity)
    session.commit()


def test_create_and_modify_to_have_required_attribute(session, unique_name):
    '''Create and modify entity to have required attribute in transaction.'''
    entity = session.create('Scope', {})
    other = session.create('Scope', {'name': unique_name})
    entity['name'] = '{0}2'.format(unique_name)
    session.commit()


def test_ignore_in_create_entity_payload_values_set_to_not_set(
    mocker, unique_name, session
):
    '''Ignore in commit, created entity data set to NOT_SET'''
    mocked = mocker.patch.object(session, '_call')

    # Should ignore 'email' attribute in payload.
    new_user = session.create(
        'User', {'username': unique_name, 'email': 'test'}
    )
    new_user['email'] = ftrack_api.symbol.NOT_SET
    session.commit()
    payloads = mocked.call_args[0][0]
    assert len(payloads) == 1


def test_ignore_operation_that_modifies_attribute_to_not_set(
    mocker, session, user
):
    '''Ignore in commit, operation that sets attribute value to NOT_SET'''
    mocked = mocker.patch.object(session, '_call')

    # Should result in no call to server.
    user['email'] = ftrack_api.symbol.NOT_SET
    session.commit()

    assert not mocked.called


def test_operation_optimisation_on_commit(session, mocker):
    '''Optimise operations on commit.'''
    mocked = mocker.patch.object(session, '_call')

    user_a = session.create('User', {'username': 'bob'})
    user_a['username'] = 'foo'
    user_a['email'] = 'bob@example.com'

    user_b = session.create('User', {'username': 'martin'})
    user_b['email'] = 'martin@ftrack.com'

    user_a['email'] = 'bob@example.com'
    user_a['first_name'] = 'Bob'

    user_c = session.create('User', {'username': 'neverexist'})
    user_c['email'] = 'ignore@example.com'
    session.delete(user_c)

    user_a_entity_key = ftrack_api.inspection.primary_key(user_a).values()
    user_b_entity_key = ftrack_api.inspection.primary_key(user_b).values()

    session.commit()

    # The above operations should have translated into three payloads to call
    # (two creates and one update).
    payloads = mocked.call_args[0][0]
    assert len(payloads) == 3

    assert payloads[0]['action'] == 'create'
    assert payloads[0]['entity_key'] == user_a_entity_key
    assert set(payloads[0]['entity_data'].keys()) == set([
        '__entity_type__', 'id', 'resource_type', 'username'
    ])

    assert payloads[1]['action'] == 'create'
    assert payloads[1]['entity_key'] == user_b_entity_key
    assert set(payloads[1]['entity_data'].keys()) == set([
        '__entity_type__', 'id', 'resource_type', 'username', 'email'
    ])

    assert payloads[2]['action'] == 'update'
    assert payloads[2]['entity_key'] == user_a_entity_key
    assert set(payloads[2]['entity_data'].keys()) == set([
        '__entity_type__', 'email', 'first_name'
    ])


def test_state_collection(session, unique_name, user):
    '''Session state collection holds correct entities.'''
    # NOT_SET
    user_a = session.create('User', {'username': unique_name})
    session.commit()

    # CREATED
    user_b = session.create('User', {'username': unique_name})
    user_b['username'] = 'changed'

    # MODIFIED
    user_c = user
    user_c['username'] = 'changed'

    # DELETED
    user_d = session.create('User', {'username': unique_name})
    session.delete(user_d)

    assert session.created == [user_b]
    assert session.modified == [user_c]
    assert session.deleted == [user_d]


def test_get_entity_with_composite_primary_key(session, new_project):
    '''Retrieve entity that uses a composite primary key.'''
    entity = session.create('Metadata', {
        'key': 'key', 'value': 'value',
        'parent_type': new_project.entity_type,
        'parent_id': new_project['id']
    })

    session.commit()

    # Avoid cache.
    new_session = ftrack_api.Session()
    retrieved_entity = new_session.get(
        'Metadata', ftrack_api.inspection.primary_key(entity).values()
    )

    assert retrieved_entity == entity


def test_get_entity_with_incomplete_composite_primary_key(session, new_project):
    '''Fail to retrieve entity using incomplete composite primary key.'''
    entity = session.create('Metadata', {
        'key': 'key', 'value': 'value',
        'parent_type': new_project.entity_type,
        'parent_id': new_project['id']
    })

    session.commit()

    # Avoid cache.
    new_session = ftrack_api.Session()
    with pytest.raises(ValueError):
        new_session.get(
            'Metadata', ftrack_api.inspection.primary_key(entity).values()[0]
        )


def test_populate_entity(session, new_user):
    '''Populate entity that uses single primary key.'''
    with session.auto_populating(False):
        assert new_user['email'] is ftrack_api.symbol.NOT_SET

    session.populate(new_user, 'email')
    assert new_user['email'] is not ftrack_api.symbol.NOT_SET


def test_populate_entities(session, unique_name):
    '''Populate multiple entities that use single primary key.'''
    users = []
    for index in range(3):
        users.append(
            session.create(
                'User', {'username': '{0}-{1}'.format(unique_name, index)}
            )
        )

    session.commit()

    with session.auto_populating(False):
        for user in users:
            assert user['email'] is ftrack_api.symbol.NOT_SET

    session.populate(users, 'email')

    for user in users:
        assert user['email'] is not ftrack_api.symbol.NOT_SET


def test_populate_entity_with_composite_primary_key(session, new_project):
    '''Populate entity that uses a composite primary key.'''
    entity = session.create('Metadata', {
        'key': 'key', 'value': 'value',
        'parent_type': new_project.entity_type,
        'parent_id': new_project['id']
    })

    session.commit()

    # Avoid cache.
    new_session = ftrack_api.Session()
    retrieved_entity = new_session.get(
        'Metadata', ftrack_api.inspection.primary_key(entity).values()
    )

    # Manually change already populated remote value so can test it gets reset
    # on populate call.
    retrieved_entity.attributes.get('value').set_remote_value(
        retrieved_entity, 'changed'
    )

    new_session.populate(retrieved_entity, 'value')
    assert retrieved_entity['value'] == 'value'


@pytest.mark.parametrize('server_information, compatible', [
    ({}, False),
    ({'version': '3.2.1'}, True),
    ({'version': '3.2.2'}, True),
    ({'version': '3.2'}, False),
    ({'version': '3.4'}, False)
], ids=[
    'No information',
    'Valid current version',
    'Valid higher version',
    'Invalid higher version',
    'Invalid lower version'
])
def test_check_server_compatibility(
    server_information, compatible, session
):
    '''Check server compatibility.'''
    with mock.patch.dict(
        session._server_information, server_information, clear=True
    ):
        if compatible:
            session.check_server_compatibility()
        else:
            with pytest.raises(ftrack_api.exception.ServerCompatibilityError):
                session.check_server_compatibility()


def test_encode_entity_using_all_attributes_strategy(mocked_schema_session):
    '''Encode entity using "all" entity_attribute_strategy.'''
    new_bar = mocked_schema_session.create(
        'Bar',
        {
            'name': 'myBar',
            'id': 'bar_unique_id'
        }
    )

    new_foo = mocked_schema_session.create(
        'Foo',
        {
            'id': 'a_unique_id',
            'string': 'abc',
            'integer': 42,
            'number': 12345678.9,
            'boolean': False,
            'date': arrow.get('2015-11-18 15:24:09'),
            'bars': [new_bar]
        }
    )

    encoded = mocked_schema_session.encode(
        new_foo, entity_attribute_strategy='all'
    )

    assert encoded == textwrap.dedent('''
        {"__entity_type__": "Foo",
         "bars": [{"__entity_type__": "Bar", "id": "bar_unique_id"}],
         "boolean": false,
         "date": {"__type__": "datetime", "value": "2015-11-18T15:24:09+00:00"},
         "id": "a_unique_id",
         "integer": 42,
         "number": 12345678.9,
         "string": "abc"}
    ''').replace('\n', '')


def test_encode_entity_using_only_set_attributes_strategy(
    mocked_schema_session
):
    '''Encode entity using "set_only" entity_attribute_strategy.'''
    new_foo = mocked_schema_session.create(
        'Foo',
        {
            'id': 'a_unique_id',
            'string': 'abc',
            'integer': 42
        }
    )

    encoded = mocked_schema_session.encode(
        new_foo, entity_attribute_strategy='set_only'
    )

    assert encoded == textwrap.dedent('''
        {"__entity_type__": "Foo",
         "id": "a_unique_id",
         "integer": 42,
         "string": "abc"}
    ''').replace('\n', '')


def test_encode_entity_using_only_modified_attributes_strategy(
    mocked_schema_session
):
    '''Encode entity using "modified_only" entity_attribute_strategy.'''
    new_foo = mocked_schema_session._create(
        'Foo',
        {
            'id': 'a_unique_id',
            'string': 'abc',
            'integer': 42
        },
        reconstructing=True
    )

    new_foo['string'] = 'Modified'

    encoded = mocked_schema_session.encode(
        new_foo, entity_attribute_strategy='modified_only'
    )

    assert encoded == textwrap.dedent('''
        {"__entity_type__": "Foo",
         "id": "a_unique_id",
         "string": "Modified"}
    ''').replace('\n', '')


def test_encode_entity_using_invalid_strategy(session, new_task):
    '''Fail to encode entity using invalid strategy.'''
    with pytest.raises(ValueError):
        session.encode(new_task, entity_attribute_strategy='invalid')


def test_decode_partial_entity(
    session, new_task
):
    '''Decode partially encoded entity.'''
    encoded = session.encode(
        new_task, entity_attribute_strategy='set_only'
    )

    entity = session.decode(encoded)

    assert entity == new_task
    assert entity is not new_task


def test_reset(mocker):
    '''Reset session.'''
    plugin_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'fixture', 'plugin')
    )
    session = ftrack_api.Session(plugin_paths=[plugin_path])

    assert hasattr(session.types.get('User'), 'stub')
    location = session.query('Location where name is "test.location"').one()
    assert location.accessor is not ftrack_api.symbol.NOT_SET

    mocked_close = mocker.patch.object(session._request, 'close')
    mocked_fetch = mocker.patch.object(session, '_load_schemas')

    session.reset()

    # Assert custom entity type maintained.
    assert hasattr(session.types.get('User'), 'stub')

    # Assert location plugin re-configured.
    location = session.query('Location where name is "test.location"').one()
    assert location.accessor is not ftrack_api.symbol.NOT_SET

    # Assert connection not closed and no schema fetch issued.
    assert not mocked_close.called
    assert not mocked_fetch.called


def test_rollback_scalar_attribute_change(session, new_user):
    '''Rollback scalar attribute change via session.'''
    assert not session.recorded_operations
    current_first_name = new_user['first_name']

    new_user['first_name'] = 'NewName'
    assert new_user['first_name'] == 'NewName'
    assert session.recorded_operations

    session.rollback()

    assert not session.recorded_operations
    assert new_user['first_name'] == current_first_name


def test_rollback_collection_attribute_change(session, new_user):
    '''Rollback collection attribute change via session.'''
    assert not session.recorded_operations
    current_timelogs = new_user['timelogs']
    assert list(current_timelogs) == []

    timelog = session.create('Timelog', {})
    new_user['timelogs'].append(timelog)
    assert list(new_user['timelogs']) == [timelog]
    assert session.recorded_operations

    session.rollback()

    assert not session.recorded_operations
    assert list(new_user['timelogs']) == []


def test_rollback_entity_creation(session):
    '''Rollback entity creation via session.'''
    assert not session.recorded_operations

    new_user = session.create('User')
    assert session.recorded_operations
    assert new_user in session.created

    session.rollback()

    assert not session.recorded_operations
    assert new_user not in session.created
    assert new_user not in session._local_cache.values()


def test_rollback_entity_deletion(session, new_user):
    '''Rollback entity deletion via session.'''
    assert not session.recorded_operations

    session.delete(new_user)
    assert session.recorded_operations
    assert new_user in session.deleted

    session.rollback()
    assert not session.recorded_operations
    assert new_user not in session.deleted
    assert new_user in session._local_cache.values()


# Caching
# ------------------------------------------------------------------------------


def test_get_entity_bypassing_cache(session, user, mocker):
    '''Retrieve an entity by type and id bypassing cache.'''
    mocker.patch.object(session, '_call', wraps=session._call)

    session.cache.remove(
        session.cache_key_maker.key(ftrack_api.inspection.identity(user))
    )

    matching = session.get(*ftrack_api.inspection.identity(user))

    # Check a different instance returned.
    assert matching is not user

    # Check instances have the same identity.
    assert matching == user

    # Check cache was bypassed and server was called.
    assert session._call.called


def test_get_entity_from_cache(cache, task, mocker):
    '''Retrieve an entity by type and id from cache.'''
    session = ftrack_api.Session(cache=cache)

    # Prepare cache.
    session.merge(task)

    # Disable server calls.
    mocker.patch.object(session, '_call')

    # Retrieve entity from cache.
    entity = session.get(*ftrack_api.inspection.identity(task))

    assert entity is not None, 'Failed to retrieve entity from cache.'
    assert entity == task
    assert entity is not task

    # Check that no call was made to server.
    assert not session._call.called


def test_get_entity_tree_from_cache(cache, new_project_tree, mocker):
    '''Retrieve an entity tree from cache.'''
    session = ftrack_api.Session(cache=cache)

    # Prepare cache.
    # TODO: Maybe cache should be prepopulated for a better check here.
    session.query(
        'select children, children.children, children.children.children, '
        'children.children.children.assignments, '
        'children.children.children.assignments.resource '
        'from Project where id is "{0}"'
        .format(new_project_tree['id'])
    ).one()

    # Disable server calls.
    mocker.patch.object(session, '_call')

    # Retrieve entity from cache.
    entity = session.get(*ftrack_api.inspection.identity(new_project_tree))

    assert entity is not None, 'Failed to retrieve entity from cache.'
    assert entity == new_project_tree
    assert entity is not new_project_tree

    # Check tree.
    with session.auto_populating(False):
        for sequence in entity['children']:
            for shot in sequence['children']:
                for task in shot['children']:
                    assignments = task['assignments']
                    for assignment in assignments:
                        resource = assignment['resource']

                        assert resource is not ftrack_api.symbol.NOT_SET

    # Check that no call was made to server.
    assert not session._call.called


def test_get_metadata_from_cache(session, mocker, cache, new_task):
    '''Retrieve an entity along with its metadata from cache.'''
    new_task['metadata']['key'] = 'value'
    session.commit()

    fresh_session = ftrack_api.Session(cache=cache)

    # Prepare cache.
    fresh_session.query(
        'select metadata.key, metadata.value from '
        'Task where id is "{0}"'
        .format(new_task['id'])
    ).all()

    # Disable server calls.
    mocker.patch.object(fresh_session, '_call')

    # Retrieve entity from cache.
    entity = fresh_session.get(*ftrack_api.inspection.identity(new_task))

    assert entity is not None, 'Failed to retrieve entity from cache.'
    assert entity == new_task
    assert entity is not new_task

    # Check metadata cached correctly.
    with fresh_session.auto_populating(False):
        metadata = entity['metadata']
        assert metadata['key'] == 'value'

    assert not fresh_session._call.called


def test_merge_circular_reference(cache, temporary_file):
    '''Merge circular reference into cache.'''
    session = ftrack_api.Session(cache=cache)
    # The following will test the condition as a FileComponent will be created
    # with corresponding ComponentLocation. The server will return the file
    # component data with the component location embedded. The component
    # location will in turn have an embedded reference to the file component.
    # If the merge does not prioritise the primary keys of the instance then
    # any cache that relies on using the identity of the file component will
    # fail.
    component = session.create_component(path=temporary_file)
    assert component


def test_correct_file_type_on_sequence_component(session):
    '''Create sequence component with correct file type.'''
    path = '/path/to/image/sequence.%04d.dpx [1-10]'
    sequence_component = session.create_component(path)

    assert sequence_component['file_type'] == '.dpx'


def test_read_schemas_from_cache(
    session, temporary_valid_schema_cache
):
    '''Read valid content from schema cache.'''
    expected_hash = 'ccf8eae8775640c7d23c93e7bcef4284'

    schemas, hash_ = session._read_schemas_from_cache(
        temporary_valid_schema_cache
    )

    assert expected_hash == hash_


def test_fail_to_read_schemas_from_invalid_cache(
    session, temporary_invalid_schema_cache
):
    '''Fail to read invalid content from schema cache.'''
    with pytest.raises(ValueError):
        session._read_schemas_from_cache(
            temporary_invalid_schema_cache
        )


def test_write_schemas_to_cache(
    session, temporary_valid_schema_cache
):
    '''Write valid content to schema cache.'''
    expected_hash = 'ccf8eae8775640c7d23c93e7bcef4284'
    schemas, _ = session._read_schemas_from_cache(temporary_valid_schema_cache)

    session._write_schemas_to_cache(schemas, temporary_valid_schema_cache)

    schemas, hash_ = session._read_schemas_from_cache(
        temporary_valid_schema_cache
    )

    assert expected_hash == hash_


def test_fail_to_write_invalid_schemas_to_cache(
    session, temporary_valid_schema_cache
):
    '''Fail to write invalid content to schema cache.'''
    # Datetime not serialisable by default.
    invalid_content = datetime.datetime.now()

    with pytest.raises(TypeError):
        session._write_schemas_to_cache(
            invalid_content, temporary_valid_schema_cache
        )


def test_load_schemas_from_valid_cache(
    mocker, session, temporary_valid_schema_cache, mocked_schemas
):
    '''Load schemas from cache.'''
    expected_schemas = session._load_schemas(temporary_valid_schema_cache)

    mocked = mocker.patch.object(session, '_call')
    schemas = session._load_schemas(temporary_valid_schema_cache)

    assert schemas == expected_schemas
    assert not mocked.called


def test_load_schemas_from_server_when_cache_invalid(
    mocker, session, temporary_invalid_schema_cache
):
    '''Load schemas from server when cache invalid.'''
    mocked = mocker.patch.object(session, '_call', wraps=session._call)

    session._load_schemas(temporary_invalid_schema_cache)
    assert mocked.called


def test_load_schemas_from_server_when_cache_outdated(
    mocker, session, temporary_valid_schema_cache
):
    '''Load schemas from server when cache outdated.'''
    schemas, _ = session._read_schemas_from_cache(temporary_valid_schema_cache)
    schemas.append({
        'id': 'NewTest'
    })
    session._write_schemas_to_cache(schemas, temporary_valid_schema_cache)

    mocked = mocker.patch.object(session, '_call', wraps=session._call)
    session._load_schemas(temporary_valid_schema_cache)

    assert mocked.called


def test_load_schemas_bypassing_cache(
    mocker, session, temporary_valid_schema_cache
):
    '''Load schemas bypassing cache when set to False.'''
    with mocker.patch.object(session, '_call'):

        session._load_schemas(temporary_valid_schema_cache)
        assert session._call.call_count == 1

        session._load_schemas(False)
        assert session._call.call_count == 2
