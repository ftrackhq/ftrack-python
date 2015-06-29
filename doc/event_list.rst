..
    :copyright: Copyright (c) 2014 ftrack

.. _event_list:

**********
Event list
**********

The following is a consolidated list of events published directly by this API.

For some events, a template plugin file is also listed for download
(:guilabel:`Download template plugin`) to help get you started with writing your
own plugin for a particular event.

.. seealso::

    * :ref:`handling_events`
    * :ref:`ftrack server event list <ftrack:developing/events/list>`

.. _event_list/ftrack.api.session.construct-entity-type:

ftrack.api.session.construct-entity-type
========================================

:download:`Download template plugin
</../resource/plugin/construct_entity_type.py>`

:ref:`Synchronous <handling_events/publishing/synchronously>`. Published by
the session to retrieve constructed class for specified schema::

    Event(
        topic='ftrack.api.session.construct-entity-type',
        data=dict(
            schema=schema,
            schemas=schemas
        )
    )

Expects returned data to be::

    A Python class.

.. seealso:: :ref:`working_with_entities/entity_types`.

.. _event_list/ftrack.api.session.configure-location:

ftrack.api.session.configure-location
=====================================

:download:`Download template plugin
</../resource/plugin/configure_locations.py>`

:ref:`Synchronous <handling_events/publishing/synchronously>`. Published by
the session to allow configuring of location instances::

    Event(
        topic='ftrack.api.session.configure-location',
        data=dict(
            session=self
        )
    )

.. seealso:: :ref:`Configuring locations <locations/configuring/automatically>`.

.. _event_list/ftrack.location.component-added:

ftrack.location.component-added
===============================

Published whenever a component is added to a location::

    Event(
        topic='ftrack.location.component-added',
        data=dict(
            componentId='e2dc0524-b576-11d3-9612-080027331d74',
            locationId='07b82a97-8cf9-11e3-9383-20c9d081909b'
        )
    )

.. _event_list/ftrack.location.component-removed:

ftrack.location.component-removed
=================================

Published whenever a component is removed from a location::

    Event(
        topic='ftrack.location.component-added',
        data=dict(
            componentId='e2dc0524-b576-11d3-9612-080027331d74',
            locationId='07b82a97-8cf9-11e3-9383-20c9d081909b'
        )
    )
