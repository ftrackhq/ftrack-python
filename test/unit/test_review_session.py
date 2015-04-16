# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack


def test_add_remove_review_session(session, unique_name):
    '''Test add and remove new review session to project.'''
    project = session.query(
        'Project where id is 5671dcb0-66de-11e1-8e6e-f23c91df25eb'
    )[0]

    review_session_count = len(project['review_sessions'])

    review_session = session.create('ReviewSession', {
        'name': unique_name,
        'description': unique_name,
        'project': project
    })

    session.commit()

    assert review_session, 'Review session created successfully.'

    assert (
        (review_session_count + 1) == len(project['review_sessions']),
        'Correct number of review sessions on project.'
    )

    # TODO: Add delete to the test. Not possible at the moment due to API
    # permissions not having the same options as PROJECT permissions.
    # New API does not seem to support the use of personal API keys either.

    # review_session_id = review_session['id']

    # session.delete(review_session)
    # session.commit()

    # review_session = session.get('ReviewSession', review_session_id)

    # assert not review_session, 'Review session removed successfully.'


def test_add_remove_review_session_objects(
    session, new_review_session, unique_name
):
    '''Test add and remove objects from review session.'''
    assert new_review_session, 'New review session available.'

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

    session.commit()

    assert review_session_object, 'Review session object created successfully.'

    review_session_objects = new_review_session['review_session_objects']

    assert (
        len(review_session_objects) == 1,
        'Correct number of objects on review session.'
    )


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
