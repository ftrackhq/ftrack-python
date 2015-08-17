..
    :copyright: Copyright (c) 2014 ftrack

.. _example/custom_attribute:

***********************
Using custom attributes
***********************

.. currentmodule:: ftrack_api.session

Custom attributes can be written and read from entities using the
custom_attribute property.

The custom_attribute property has a similar interface as a dictionary and keys
can be printed using the keys method::

    >>> task['custom_attributes'].keys()
    [u'my_text_field']

or items::

    >>> print task['custom_attributes'].items()
    [(u'my_text_field', u'some text')]

Read existing custom attributes::

    >>> print task['custom_attributes']['my_text_field']
    'some text'

Setting custom attributes can be done in several ways. The first example below 
will only update a singe attribute, while the second way will completely replace
any existing custom_attribute::

    task['custom_attributes']['my_text_field'] = 'foo'
    task['custom_attributes'] = {
        'my_text_field': 'bar'
    }

Limitations
===========

Expression attributes
---------------------

Expression attributes are not yet supported and the reported value will
always be the non-evaluated expression.

Hierarchical attributes
-----------------------

Hierarchical attributes are not yet supported and can not be read or updated
using the API.

Type conversion
---------------

Custom attributes will always be returned as unicode strings from the API, 
even though configured as e.g. a boolean and will need to be converted
manually.

Validation
==========

Custom attributes are validated on the ftrack server before persisted. The
validation will check that the type of the data is correct for the custom
attribute.

    * number - :py:class:`int` or :py:class:`float`
    * text - :py:class:`str` or :py:class:`unicode`
    * enumerator - :py:class:`list`
    * boolean - :py:class:`bool`
    * date - :py:class:`datetime.datetime` or :py:class:`datetime.date`

If the value set is not valid a :py:exc:`ftrack_api.exception.ServerError` is
raised with debug information::

    shot['custom_attributes']['fstart'] = 'test'

    Traceback (most recent call last):
        ...
    ftrack_api.exception.ServerError: Server reported error: 
    ValidationError(Custom attribute value for "fstart" must be of type number.
    Got "test" of type <type 'unicode'>)