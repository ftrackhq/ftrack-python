..
    :copyright: Copyright (c) 2014 ftrack

.. _release/release_notes:

*************
Release Notes
*************

.. currentmodule:: ftrack_api.session

.. release:: 0.6.0
    :date: 2015-08-19

    .. change:: changed
        :tags: server version

        ftrack server version >= 3.1.8, < 3.2 required.

    .. change:: changed
        :tags: querying, documentation

        Updated documentation with details on new operators ``has`` and ``any``
        for querying relationships.

        .. seealso:: :ref:`querying/criteria/operators`

.. release:: 0.5.2
    :date: 2015-07-29

    .. change:: changed
        :tags: server version

        ftrack server version 3.1.5 or greater required.

    .. change:: changed

        Server reported errors are now more readable and are no longer sometimes
        presented as an HTML page.

.. release:: 0.5.1
    :date: 2015-07-06

    .. change:: changed

        Defaults computed by :class:`~ftrack_api.entity.factory.StandardFactory`
        are now memoised per session to improve performance.

    .. change:: changed

        :class:`~ftrack_api.cache.Memoiser` now supports a *return_copies*
        parameter to control whether deep copies should be returned when a value
        was retrieved from the cache.

.. release:: 0.5.0
    :date: 2015-07-02

    .. change:: changed

        Now checks for server compatibility and requires an ftrack server
        version of 3.1 or greater.

    .. change:: new

        Added convenience methods to :class:`~ftrack_api.query.QueryResult` to
        fetch :meth:`~ftrack_api.query.QueryResult.first` or exactly
        :meth:`~ftrack_api.query.QueryResult.one` result.

    .. change:: new
        :tags: notes

        Added support for handling notes.

        .. seealso:: :ref:`example/note`.

    .. change:: changed

        Collection attributes generate empty collection on first access when no
        remote value available. This allows interacting with a collection on a
        newly created entity before committing.

    .. change:: fixed
        :tags: session

        Ambiguous error raised when :class:`Session` is started with an invalid
        user or key.

    .. change:: fixed
        :tags: caching, session

        :meth:`Session.merge` fails against
        :class:`~ftrack_api.cache.SerialisedCache` when circular reference
        encountered due to entity identity not being prioritised in merge.

.. release:: 0.4.3
    :date: 2015-06-29

    .. change:: fixed
        :tags: plugins, session, entity types

        Entity types not constructed following standard install.

        This is because the discovery of the default plugins is unreliable
        across Python installation processes (pip, wheel etc). Instead, the
        default plugins have been added as templates to the :ref:`event_list`
        documentation and the
        :class:`~ftrack_api.entity.factory.StandardFactory` used to create any
        missing classes on :class:`Session` startup.

.. release:: 0.4.2
    :date: 2015-06-26

    .. change:: fixed
        :tags: metadata

        Setting exact same metadata twice can cause
        :exc:`~ftrack_api.exception.ImmutableAttributeError` to be incorrectly
        raised.

    .. change:: fixed
        :tags: session

        Calling :meth:`Session.commit` does not clear locally set attribute
        values leading to immutability checks being bypassed in certain cases.

.. release:: 0.4.1
    :date: 2015-06-25

    .. change:: fixed
        :tags: metadata

        Setting metadata twice in one session causes `KeyError`.

.. release:: 0.4.0
    :date: 2015-06-22

    .. change:: changed
        :tags: documentation

        Documentation extensively updated.

    .. change:: new
        :tags: Client review
        
        Added support for handling review sessions.

        .. seealso:: :ref:`Usage guide <example/review_session>`.

    .. change:: fixed

        Metadata property not working in line with rest of system, particularly
        the caching framework.

    .. change:: new
        :tags: collection

        Added :class:`ftrack_api.collection.MappedCollectionProxy` class for
        providing a dictionary interface to a standard
        :class:`ftrack_api.collection.Collection`.

    .. change:: new
        :tags: collection, attribute

        Added :class:`ftrack_api.attribute.MappedCollectionAttribute` class for
        describing an attribute that should use the
        :class:`ftrack_api.collection.MappedCollectionProxy`.

    .. change:: new

        Entities that use composite primary keys are now fully supported in the
        session, including for :meth:`Session.get` and :meth:`Session.populate`.

    .. change:: change

        Base :class:`ftrack_api.entity.factory.Factory` refactored to separate
        out attribute instantiation into dedicated methods to make extending
        simpler.

    .. change:: change
        :tags: collection, attribute

        :class:`ftrack_api.attribute.DictionaryAttribute` and
        :class:`ftrack_api.attribute.DictionaryAttributeCollection` removed.
        They have been replaced by the new
        :class:`ftrack_api.attribute.MappedCollectionAttribute` and
        :class:`ftrack_api.collection.MappedCollectionProxy` respectively.

    .. change:: new
        :tags: events

        :class:`Session` now supports an *auto_connect_event_hub* argument to
        control whether the built in event hub should connect to the server on
        session initialisation. This is useful for when only local events should
        be supported or when the connection should be manually controlled.

.. release:: 0.3.0
    :date: 2015-06-14

    .. change:: fixed

        Session operations may be applied server side in invalid order resulting
        in unexpected error.

    .. change:: fixed

        Creating and deleting an entity in single commit causes error as create
        operation never persisted to server.

        Now all operations for the entity are ignored on commit when this case
        is detected.

    .. change:: changed

        Internally moved from differential state to operation tracking for
        determining session changes when persisting.

    .. change:: new

        ``Session.recorded_operations`` attribute for examining current
        pending operations on a :class:`Session`.

    .. change:: new

        :meth:`Session.operation_recording` context manager for suspending
        recording operations temporarily. Can also manually control
        ``Session.record_operations`` boolean.

    .. change:: new

        Operation classes to track individual operations occurring in session.

    .. change:: new

        Public :meth:`Session.merge` method for merging arbitrary values into
        the session manually.

    .. change:: changed

        An entity's state is now computed from the operations performed on it
        and is no longer manually settable.

    .. change:: changed

        ``Entity.state`` attribute removed. Instead use the new inspection
        :func:`ftrack_api.inspection.state`.

        Previously::

            print entity.state

        Now::

            import ftrack_api.inspection
            print ftrack_api.inspection.state(entity)

        There is also an optimised inspection,
        :func:`ftrack_api.inspection.states`. for determining state of many
        entities at once.

    .. change:: changed

        Shallow copying a :class:`ftrack_api.symbol.Symbol` instance now
        returns same instance.

.. release:: 0.2.0
    :date: 2015-06-04

    .. change:: changed

        Changed name of API from `ftrack` to `ftrack_api`.

        .. seealso:: :ref:`release/migration/0.2.0/new_api_name`.

    .. change:: new
        :tags: caching

        Configurable caching support in :class:`Session`, including the ability
        to use an external persisted cache and new cache implementations.

        .. seealso:: :ref:`caching`.

    .. change:: new
        :tags: caching

        :meth:`Session.get` now tries to retrieve matching entity from
        configured cache first.

    .. change:: new
        :tags: serialisation, caching

        :meth:`Session.encode` supports a new mode *persisted_only* that will
        only encode persisted attribute values.

    .. change:: changed

        Session.merge method is now private (:meth:`Session._merge`) until it is
        qualified for general usage.

    .. change:: changed
        :tags: entity state

        :class:`~ftrack_api.entity.base.Entity` state now managed on the entity
        directly rather than stored separately in the :class:`Session`.

        Previously::

            session.set_state(entity, state)
            print session.get_state(entity)

        Now::

            entity.state = state
            print entity.state

    .. change:: changed
        :tags: entity state

        Entity states are now :class:`ftrack_api.symbol.Symbol` instances rather
        than strings.

        Previously::

            entity.state = 'created'

        Now::

            entity.state = ftrack_api.symbol.CREATED

    .. change:: fixed
        :tags: entity state

        It is now valid to transition from most entity states to an
        :attr:`ftrack_api.symbol.NOT_SET` state.

    .. change:: changed
        :tags: caching

        :class:`~ftrack_api.cache.EntityKeyMaker` removed and replaced by
        :class:`~ftrack_api.cache.StringKeyMaker`. Entity identity now
        computed separately and passed to key maker to allow key maker to work
        with non entity instances.

    .. change:: fixed
        :tags: entity

        Internal data keys ignored when re/constructing entities reducing
        distracting and irrelevant warnings in logs.

    .. change:: fixed
        :tags: entity

        :class:`~ftrack_api.entity.base.Entity` equality test raises error when
        other is not an entity instance.

    .. change:: changed
        :tags: entity, caching

        :meth:`~ftrack_api.entity.base.Entity.merge` now also merges state and
        local attributes. In addition, it ensures values being merged have also
        been merged into the session and outputs more log messages.

    .. change:: fixed
        :tags: inspection

        :func:`ftrack_api.inspection.identity` returns different result for same
        entity depending on whether entity type is unicode or string.

    .. change:: fixed

        :func:`ftrack_api.mixin` causes method resolution failure when same
        class mixed in multiple times.

    .. change:: changed

        Representations of objects now show plain id rather than converting to
        hex.

    .. change:: fixed
        :tags: events

        Event hub raises TypeError when listening to ftrack.update events.

    .. change:: fixed
        :tags: events

        :meth:`ftrack_api.event.hub.EventHub.subscribe` fails when subscription
        argument contains special characters such as `@` or `+`.

    .. change:: fixed
        :tags: collection

        :meth:`ftrack_api.collection.Collection` incorrectly modifies entity
        state on initialisation.

.. release:: 0.1.0
    :date: 2015-03-25

    .. change:: changed

        Moved standardised construct entity type logic to core package (as part
        of the :class:`~ftrack_api.entity.factory.StandardFactory`) for easier
        reuse and extension.

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

        :meth:`Session.encode` now supports different strategies for encoding
        entities via the entity_attribute_strategy* keyword argument. This makes
        it possible to use this method for general serialisation of entity
        instances.

    .. change:: changed

        Encoded referenced entities are now a mapping containing
        *__entity_type__* and then each key, value pair that makes up the
        entity's primary key. For example::

            {
                '__entity_type__': 'User',
                'id': '8b90a444-4e65-11e1-a500-f23c91df25eb'
            }

    .. change:: changed

        :meth:`Session.decode` no longer automatically adds decoded entities to
        the :class:`Session` cache making it possible to use decode
        independently.

    .. change:: new

        Added :meth:`Session.merge` for merging entities recursively into the
        session cache.

    .. change:: fixed

        Replacing an entity in a :class:`ftrack_api.collection.Collection` with an
        identical entity no longer raises
        :exc:`ftrack_api.exception.DuplicateItemInCollectionError`.
