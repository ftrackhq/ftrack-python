..
    :copyright: Copyright (c) 2016 ftrack

.. _example/asset_version_dependency:

********************************
Using asset version depencencies
********************************

.. currentmodule:: ftrack_api.session

Asset versions can be linked together through dependencies. This is commonly
used to indicate that an Asset version is used by another Asset version. E.g.
a Model is used by a Rig.

The dependencies can be created by the use of the `uses_versions` and
`used_in_versions` relations::

    rig_version['uses_versions'].append(model_version)
    session.commit()

Which versions are using the model can then be listed with::

    for version in model_version['used_in_versions']:
        print '{0} is using {1}'.format(version, model_version)
