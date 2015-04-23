# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import uuid

import ftrack


def test_add_remove_review_session(session, unique_name):
    '''Test add and remove new review session to project.'''
    project = session.get(
        'Project', '5671dcb0-66de-11e1-8e6e-f23c91df25eb'
    )

    review_session_count = len(project['review_sessions'])

    review_session_id = str(uuid.uuid1())
    review_session = session.create('ReviewSession', {
        'id': review_session_id,
        'name': unique_name,
        'description': unique_name,
        'project': project
    })

    session.commit()

    session = ftrack.Session()

    review_session = session.get('ReviewSession', review_session_id)
    assert review_session, 'ReviewSession with id "{0}" does not exist.'.format(
        review_session_id
    )

    project_new = session.get(
        'Project', '5671dcb0-66de-11e1-8e6e-f23c91df25eb'
    )

    new_review_session_count = len(project_new['review_sessions'])
    assert(review_session_count + 1) == new_review_session_count

    session.delete(review_session)
    session.commit()

    session = ftrack.Session()

    review_session = session.get('ReviewSession', review_session_id)

    assert not review_session


def test_add_remove_review_session_objects(
    session, new_review_session, unique_name
):
    '''Test add and remove objects from review session.'''
    new_review_session_id = new_review_session['id']

    # Get a reviewable AssetVersion from the 'client review' project.
    asset_version = session.get(
        'AssetVersion', 'a7519019-5910-11e4-804a-3c0754282242'
    )

    review_session_object_id = str(uuid.uuid1())
    review_session_object = session.create('ReviewSessionObject', {
        'id': review_session_object_id,
        'name': unique_name,
        'description': unique_name,
        'version': 'Version {0}'.format(asset_version['version']),
        'asset_version': asset_version,
        'review_session': new_review_session
    })

    session.commit()

    assert review_session_object, 'Review session object created successfully.'

    review_session_objects = new_review_session['review_session_objects']

    assert len(review_session_objects) == 1

    session.delete(review_session_object)
    session.commit()

    session = ftrack.Session()

    review_session = session.get('ReviewSession', new_review_session_id)

    assert len(review_session['review_session_objects']) == 0


def test_add_object_with_append(session, new_review_session, unique_name):
    '''Test adding object using append.'''
    new_review_session_id = new_review_session['id']

    # Get a reviewable AssetVersion from the 'client review' project.
    asset_version = session.get(
        'AssetVersion', 'a7519019-5910-11e4-804a-3c0754282242'
    )

    review_session_object_id = str(uuid.uuid1())
    review_session_object = session.create('ReviewSessionObject', {
        'id': review_session_object_id,
        'name': unique_name,
        'description': unique_name,
        'version': 'Version {0}'.format(asset_version['version']),
        'asset_version': asset_version
    })

    new_review_session['review_session_objects'].append(
        review_session_object
    )

    session.commit()

    session = ftrack.Session()

    review_session = session.get('ReviewSession', new_review_session_id)
    review_session_objects = review_session['review_session_objects']

    assert len(review_session_objects) == 1


def test_remove_object_with_pop(
    session, new_review_session_object, unique_name
):
    '''Test adding object using append.'''
    review_session = new_review_session_object['review_session']
    review_session_id = review_session['id']

    review_session['review_session_objects'].pop()
    session.commit()

    session = ftrack.Session()

    review_session = session.get('ReviewSession', review_session_id)
    review_session_objects = review_session['review_session_objects']

    assert len(review_session_objects) == 0


def test_add_remove_review_session_invitee(session, new_review_session):
    '''Test add and remove invitees from review session.'''
    review_session_invitees = new_review_session['review_session_invitees']

    assert len(review_session_invitees) == 0

    review_session_invitee = session.create('ReviewSessionInvitee', {
        'email': 'john.doe@example.com',
        'name': 'John Doe',
        'review_session': new_review_session
    })

    session.commit()

    invitee_id = review_session_invitee['id']

    review_session_invitee = session.get(
        'ReviewSessionInvitee', invitee_id
    )

    assert review_session_invitee, 'Invitee created successfully.'

    assert (
        review_session_invitee['review_session_id'] == new_review_session['id']
    )

    session.delete(review_session_invitee)
    session.commit()

    review_session_invitee = session.get('ReviewSessionInvitee', invitee_id)

    assert not review_session_invitee


def test_add_invitee_with_append(session, new_review_session, unique_name):
    '''Test adding object using append.'''
    new_review_session_id = new_review_session['id']

    review_session_invitee = session.create('ReviewSessionInvitee', {
        'email': 'john.doe@example.com',
        'name': 'John Doe',
        'review_session': new_review_session
    })

    new_review_session['review_session_invitees'].append(
        review_session_invitee
    )

    session.commit()

    session = ftrack.Session()

    review_session = session.get('ReviewSession', new_review_session_id)
    review_session_objects = review_session['review_session_invitees']

    assert len(review_session_objects) == 1


def test_remove_invitee_with_pop(session, new_review_session, unique_name):
    '''Test adding object using append.'''
    review_session_id = new_review_session['id']

    session.create('ReviewSessionInvitee', {
        'email': 'john.doe@example.com',
        'name': 'John Doe',
        'review_session': new_review_session
    })

    session.commit()

    new_review_session['review_session_invitees'].pop()
    session.commit()

    session = ftrack.Session()

    review_session = session.get('ReviewSession', review_session_id)
    review_session_objects = review_session['review_session_invitees']

    assert len(review_session_objects) == 0


def test_add_remove_review_session_object_statuses(
    session, new_review_session, unique_name
):
    '''Test add, remove and updating review session object statuses.'''

    # Get a reviewable AssetVersion from the 'client review' project.
    asset_version = session.get(
        'AssetVersion', 'a7519019-5910-11e4-804a-3c0754282242'
    )

    review_session_object = session.create('ReviewSessionObject', {
        'name': unique_name,
        'description': unique_name,
        'version': 'Version {0}'.format(asset_version['version']),
        'asset_version': asset_version,
        'review_session': new_review_session
    })

    invitee = session.create('ReviewSessionInvitee', {
        'email': 'john.doe@example.com',
        'name': 'John Doe',
        'review_session': new_review_session
    })

    # Create a new status and set status to approved.
    review_session_object_status = session.create('ReviewSessionObjectStatus', {
        'status': 'approved',
        'invitee': invitee,
        'review_session_object': review_session_object
    })

    session.commit()

    assert review_session_object_status, 'Status created successfully.'

    review_session_object_status_id = review_session_object_status['id']

    session = ftrack.Session()

    object_status = session.get(
        'ReviewSessionObjectStatus', review_session_object_status_id
    )

    assert object_status['status'] == 'approved'
    assert (
        object_status['invitee']['id'] == invitee['id']
    )
