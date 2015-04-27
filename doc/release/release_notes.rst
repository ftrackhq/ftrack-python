..
    :copyright: Copyright (c) 2014 ftrack

.. _release/release_notes:

*************
Release Notes
*************

.. release:: next
        
    .. change:: new

        Changed name of API from `ftrack` to `ftrack_api`.
        :ref:`Read more <release/migration/next/new_api_name>`

    .. change:: fixed
        :tags: events

        Event hub raises TypeError when listening to ftrack.update events.

    .. change:: fixed
        :tags: events

        :meth:`ftrack_api.session.event_hub.subscribe` fails when `subscription`
        argument contains special characters such as `@` or `+`.

.. release:: 0.1.0
    :date: 2015-03-25

    .. change:: changed

        Moved standardised construct entity type logic to core package (as part
        of the :class:`~ftrack_api.entity.factory.StandardFactory`) for easier reuse
        and extension.

.. release:: 0.1.0-beta.2
    :date: 2015-03-17

    .. change:: new
        :tags: locations

        Support for ftrack.server location. The corresponding server build is
        required for it to function properly.

    .. change:: new
        :tags: locations

        Support for managing components in locations has been added. Check out
        the :ref:`dedicated tutorial <locations/tutorial>`.

    .. change:: new

        A new inspection API (:mod:`ftrack_api.inspection`) has been added for
        extracting useful information from objects in the system, such as the
        identity of an entity.

    .. change:: changed

        ``Entity.primary_key`` and ``Entity.identity`` have been removed.
        Instead, use the new :func:`ftrack_api.inspection.primary_key` and
        :func:`ftrack_api.inspection.identity` functions. This was done to make it
        clearer the the extracted information is determined from the current
        entity state and modifying the returned object will have no effect on
        the entity instance itself.

    .. change:: changed

        :func:`ftrack_api.inspection.primary_key` now returns a mapping of the
        attribute names and values that make up the primary key, rather than
        the previous behaviour of returning a tuple of just the values. To
        emulate previous behaviour do::

            ftrack_api.inspection.primary_key(entity).values()

    .. change:: changed

        :meth:`Session.encode <ftrack_api.session.Session.encode>` now supports
        different strategies for encoding entities via the
        *entity_attribute_strategy* keyword argument. This makes it possible to
        use this method for general serialisation of entity instances.

    .. change:: changed

        Encoded referenced entities are now a mapping containing
        *__entity_type__* and then each key, value pair that makes up the
        entity's primary key. For example::

            {
                '__entity_type__': 'User',
                'id': '8b90a444-4e65-11e1-a500-f23c91df25eb'
            }

    .. change:: changed

        :meth:`Session.decode <ftrack_api.session.Session.decode>` no longer
        automatically adds decoded entities to the
        :class:`~ftrack_api.session.Session` cache making it possible to use decode
        independently.

    .. change:: new

        Added :meth:`Session.merge <ftrack_api.session.Session.merge>` for merging
        entities recursively into the session cache.

    .. change:: fixed

        Replacing an entity in a :class:`ftrack_api.collection.Collection` with an
        identical entity no longer raises
        :exc:`ftrack_api.exception.DuplicateItemInCollectionError`.
