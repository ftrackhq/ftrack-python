..
    :copyright: Copyright (c) 2023 ftrack

.. _example/webhooks:

*********************
Working with Webhooks
*********************

.. currentmodule:: ftrack_api.session

Webhooks are a way to get notified when something happens in ftrack. The API
exposes a `Webhook` object that can be used to create and manage webhooks.

The following example shows how to create a webhook that will be triggered when
a task is created::

    # Create a new automation.
    automation = session.create('Automation', {
        'name': 'Task created',
    })

    # Create a trigger.
    trigger = session.create('Trigger', {
        'automation_id': automation['id'],
        'filter': 'entity.entity_type = "Task" and entity.operation = "create"',
    })

    # Create the webhook.
    webhook = session.create('WebhookAction', {
        'automation_id': automation['id'],
        "webhook_url": "https://my-custom-webhook-url.com",
    })

    session.commit()

The trigger has a filter that will be evaluated when an event happens in ftrack.
If the filter evaluates to true, the webhook will be triggered. The filter operates on
the event data and can be used to filter on any data in the event.
The whole event is included webhook when sent.

The filter supports basic syntax like `and`, `or`, `=` and `!=`.

The following example shows how to create trigger for when
the status of an AssetVersion changes to "Pending Approval"::

    # Get the status id for "Pending Approval".
    status_id = session.query(
        'select id from Status where name is "Pending Approval"'
    ).one()['id']

    # Create a trigger.
    trigger = session.create('Trigger', {
        'automation_id': automation['id'],
        'filter': f'entity.entity_type = "AssetVersion" and entity.operation = "update" and entity.new.status_id != entity.old.status_id and entity.new.status_id = "{status_id}"',
    })

In the initial release of webhooks, only entity events are supported and
only operations `create` and `update`. The events contain all
the direct properties from the API schemas for the entity in entity.new and
entity.old. The event does not contain any data for related entities or
computed properties such as URLs. For more information on what entities
exist and their properties see the API reference in your workspace. The
reference can be found by clicking your own icon in the top left corner and then
select Help.
