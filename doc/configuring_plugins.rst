..
    :copyright: Copyright (c) 2015 ftrack

.. _configuring plugins:

********************************
Configuring plugins via registry
********************************

.. currentmodule:: ftrack_api

Plugins are used by the API to extend it with new functionality, such as 
:term:`locations` or :term:`actions`. 

When the :ref:`session` is created, you have the option to specify a list of
paths to search for plugins, either as the :py:param:`plugin_paths` or
:envvar:`FTRACK_EVENT_PLUGIN_PATH`.

The directories will be searched for :term:`plugins <plugin>`, python files
which expose a :py:function:`register` function. These functions will be
evaluated and can be used extend the API with new functionality, such as 
locations or actions.

Configuring plugins via registry
================================

Quick setup
-----------

1. Create a directory where plugins will be stored. Place any plugins you want
loaded automatically in an API *session* here.

.. image:: /image/configuring_plugins_directory.png

2. Configure the :envvar:`FTRACK_EVENT_PLUGIN_PATH` to point to the directory.


Detailed setup
--------------

Start out by creating a directory on your machine where you will store your
plugins. Download :download:`example_plugin.py </resource/example_plugin.py>` and
place it in the directory.

Open up a terminal window, and ensure that plugin is picked up when
instantiating the session and manually setting the *plugin_paths*::

    >>>  # Set up basic logging
    >>> import logging
    >>> logging.basicConfig()
    >>> plugin_logger = logging.getLogger('com.example.example-plugin')
    >>> plugin_logger.setLevel(logging.DEBUG)
    >>>
    >>> # Configure the API, loading plugins in the specified paths.
    >>> import ftrack_api
    >>> plugin_paths = ['/path/to/plugins']
    >>> session = ftrack_api.Session(plugin_paths=plugin_paths)

If everything is working as expected, you should see the following in the
output::

    DEBUG:com.example.example-plugin:Plugin registered

Instead of specifying the plugin paths when instantiating the session, you can
also specify the :envvar:`FTRACK_EVENT_PLUGIN_PATH` to point to the directory.
