# :coding: utf-8
# :copyright: Copyright (c) 2013 ftrack

import os
import collections
import urlparse
import threading
import Queue as queue
import logging
import time
import getpass
import uuid
import operator
import functools
import json
import socket

import requests
import requests.exceptions
import websocket

import ftrack.exception
import ftrack.event.base
import ftrack.event.subscriber
import ftrack.event.expression


SocketIoSession = collections.namedtuple('SocketIoSession', [
    'id',
    'heartbeatTimeout',
    'supportedTransports',
])


ServerDetails = collections.namedtuple('ServerDetails', [
    'scheme',
    'hostname',
    'port',
])


class EventHub(object):
    '''Manage routing of events.'''

    def __init__(self, server=None):
        '''Initialise hub, connecting to ftrack *server*.'''
        super(EventHub, self).__init__()
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.id = uuid.uuid4().hex
        self._connection = None

        self._unique_packet_id = 0
        self._packet_callbacks = {}
        self._lock = threading.RLock()

        self._wait_timeout = 4

        self._subscribers = []
        self._reply_callbacks = {}
        self._intentional_disconnect = False

        self._event_queue = queue.Queue()
        self._event_namespace = 'ftrack.event'
        self._expression_parser = ftrack.event.expression.Parser()

        # Default values for auto reconnection timeout on unintentional
        # disconnection. Equates to 5 minutes.
        self._auto_reconnect_attempts = 30
        self._auto_reconnect_delay = 10

        # Mapping of Socket.IO codes to meaning.
        self._code_name_mapping = {
            '0': 'disconnect',
            '1': 'connect',
            '2': 'heartbeat',
            '3': 'message',
            '4': 'json',
            '5': 'event',
            '6': 'acknowledge',
            '7': 'error'
        }
        self._code_name_mapping.update(
            dict((name, code) for code, name in self._code_name_mapping.items())
        )

        # Parse server URL and store server details.
        if server is None:
            server = os.environ.get('FTRACK_SERVER')

        if not server:
            raise TypeError(
                'Required "server" not specified. Pass as argument or set '
                'in environment variable FTRACK_SERVER.'
            )

        url_parse_result = urlparse.urlparse(server)
        self.server = ServerDetails(
            url_parse_result.scheme,
            url_parse_result.hostname,
            8002
        )

    def get_server_url(self):
        '''Return URL to server.'''
        return '{0}://{1}:{2}'.format(*self.server)

    @property
    def secure(self):
        '''Return whether secure connection used.'''
        return self.server.scheme == 'https'

    def connect(self):
        '''Initialise connection to server.

        Raise :exc:`ftrack.exception.EventHubConnectionError` if already
        connected or connection fails.

        '''
        if self.connected:
            raise ftrack.exception.EventHubConnectionError(
                'Already connected.'
            )

        # Reset flag tracking whether disconnection was intentional.
        self._intentional_disconnect = False

        try:
            # Connect to socket.io server using websocket transport.
            session = self._get_socket_io_session()

            if 'websocket' not in session.supportedTransports:
                raise ValueError(
                    'Server does not support websocket sessions.'
                )

            scheme = 'wss' if self.secure else 'ws'
            url = '{0}://{1}:{2}/socket.io/1/websocket/{3}'.format(
                scheme, self.server.hostname, self.server.port, session.id
            )
            self._connection = websocket.create_connection(url)

        except Exception:
            self.logger.debug(
                'Error connecting to event server at {0}.'
                .format(self.get_server_url()),
                exc_info=1
            )
            raise ftrack.exception.EventHubConnectionError(
                'Failed to connect to event server at {0}.'
                .format(self.get_server_url())
            )

        # Start background processing thread.
        self._processor_thread = _ProcessorThread(self)
        self._processor_thread.start()

        # Subscribe to reply events if not already. Note: Only adding the
        # subscriber locally as the following block will notify server of all
        # existing subscribers, which would cause the server to report a
        # duplicate subscriber error if EventHub.subscribe was called here.
        try:
            self._add_subscriber(
                'topic=ftrack.meta.reply',
                self._handle_reply,
                subscriber=dict(
                    id=self.id
                )
            )
        except ftrack.exception.NotUniqueError:
            pass

        # Now resubscribe any existing stored subscribers. This can happen when
        # reconnecting automatically for example.
        for subscriber in self._subscribers[:]:
            self._notify_server_about_subscriber(subscriber)

    @property
    def connected(self):
        '''Return if connected.'''
        return self._connection is not None and self._connection.connected

    def disconnect(self, unsubscribe=True):
        '''Disconnect from server.

        Raise :exc:`ftrack.exception.EventHubConnectionError` if not
        currently connected.

        If *unsubscribe* is True then unsubscribe all current subscribers
        automatically before disconnecting.

        '''
        if not self.connected:
            raise ftrack.exception.EventHubConnectionError(
                'Not currently connected.'
            )

        else:
            # Set flag to indicate disconnection was intentional.
            self._intentional_disconnect = True

            # # Unsubscribe all subscribers.
            if unsubscribe:
                for subscriber in self._subscribers[:]:
                    self.unsubscribe(subscriber.metadata['id'])

                # Wait briefly to allow unsubscribe messages to be sent.
                time.sleep(self._wait_timeout)

            # Shutdown background processing thread.
            self._processor_thread.cancel()

            # Join to it if it is not current thread to help ensure a clean
            # shutdown.
            if threading.current_thread() != self._processor_thread:
                self._processor_thread.join(self._wait_timeout)

            # Now disconnect.
            self._connection.close()
            self._connection = None

    def reconnect(self, attempts=10, delay=5):
        '''Reconnect to server.

         Make *attempts* number of attempts with *delay* in seconds between each
         attempt.

        .. note::

            All current subscribers will be automatically resubscribed after
            successful reconnection.

        Raise :exc:`ftrack.exception.EventHubConnectionError` if fail to
        reconnect.

        '''
        try:
            self.disconnect(unsubscribe=False)
        except ftrack.exception.EventHubConnectionError:
            pass

        for attempt in range(attempts):
            self.logger.debug(
                'Reconnect attempt {0} of {1}'.format(attempt, attempts)
            )

            # Silence logging temporarily to avoid lots of failed connection
            # related information.
            try:
                logging.disable(logging.CRITICAL)

                try:
                    self.connect()
                except ftrack.exception.EventHubConnectionError:
                    time.sleep(delay)
                else:
                    break

            finally:
                logging.disable(logging.NOTSET)

        if not self.connected:
            raise ftrack.exception.EventHubConnectionError(
                'Failed to reconnect to event server at {0} after {1} attempts.'
                .format(self.get_server_url(), attempts)
            )

    def wait(self, duration=None):
        '''Wait for events and handle as they arrive.

        If *duration* is specified, then only process events until duration is
        reached. *duration* is in seconds though float values can be used for
        smaller values.

        '''
        started = time.time()

        while True:
            try:
                event = self._event_queue.get(timeout=0.1)
            except queue.Empty:
                pass
            else:
                self._handle(event)

                # Additional special processing of events.
                if event['topic'] == 'ftrack.meta.disconnected':
                    break

            if duration is not None:
                if (time.time() - started) > duration:
                    break

    def get_subscriber_by_identifier(self, identifier):
        '''Return subscriber with matching *identifier*.

        Return None if no subscriber with *identifier* found.

        '''
        for subscriber in self._subscribers[:]:
            if subscriber.metadata.get('id') == identifier:
                return subscriber

        return None

    def subscribe(self, subscription, callback, subscriber=None, priority=100):
        '''Register *callback* for *subscription*.

        A *subscription* is a string that can specify in detail which events the
        callback should receive. The filtering is applied against each event
        object. Nested references are supported using '.' separators.
        For example, 'topic=foo and data.eventType=Shot' would match the
        following event::

            <Event {'topic': 'foo', 'data': {'eventType': 'Shot'}}>

        The *callback* should accept an instance of
        :class:`ftrack.event.base.Event` as its sole argument.

        Callbacks are called in order of *priority*. The lower the priority
        number the sooner it will be called, with 0 being the first. The
        default priority is 100. Note that priority only applies against other
        callbacks registered with this hub and not as a global priority.

        An earlier callback can prevent processing of subsequent callbacks by
        calling :meth:`Event.stop` on the passed `event` before
        returning.

        .. warning::

            Handlers block processing of other received events. For long
            running callbacks it is advisable to delegate the main work to
            another process or thread.

        A *callback* can be attached to *subscriber* information that details
        the subscriber context. A subscriber context will be generated
        automatically if not supplied.

        .. note::

            The subscription will be stored locally, but until the server
            receives notification of the subscription it is possible the
            callback will not be called.

        Return subscriber identifier.

        Raise :exc:`ftrack.exception.NotUniqueError` if a subscriber with the
        same identifier already exists.

        '''
        # Add subscriber locally.
        subscriber = self._add_subscriber(
            subscription, callback, subscriber, priority
        )

        # Notify server now if possible.
        try:
            self._notify_server_about_subscriber(subscriber)
        except ftrack.exception.EventHubConnectionError:
            self.logger.debug(
                'Failed to notify server about new subscriber {0} '
                'as server not currently reachable.'
                .format(subscriber.metadata['id'])
            )

        return subscriber.metadata['id']

    def _add_subscriber(
        self, subscription, callback, subscriber=None, priority=100
    ):
        '''Add subscriber locally.

        See :meth:`subscribe` for argument descriptions.

        Return :class:`ftrack.event.subscriber.Subscriber` instance.

        Raise :exc:`ftrack.exception.NotUniqueError` if a subscriber with the
        same identifier already exists.

        '''
        if subscriber is None:
            subscriber = {}

        subscriber.setdefault('id', uuid.uuid4().hex)

        # Check subscriber not already subscribed.
        existing_subscriber = self.get_subscriber_by_identifier(
            subscriber['id']
        )

        if existing_subscriber is not None:
            raise ftrack.exception.NotUniqueError(
                'Subscriber with identifier {0} already exists.'
                .format(subscriber['id'])
            )

        subscriber = ftrack.event.subscriber.Subscriber(
            subscription=subscription,
            callback=callback,
            metadata=subscriber,
            priority=priority
        )

        self._subscribers.append(subscriber)

        return subscriber

    def _notify_server_about_subscriber(self, subscriber):
        '''Notify server of new *subscriber*.'''
        subscribe_event = ftrack.event.base.Event(
            topic='ftrack.meta.subscribe',
            data=dict(
                subscriber=subscriber.metadata,
                subscription=str(subscriber.subscription)
            )
        )

        self._publish(
            subscribe_event,
            callback=functools.partial(self._on_subscribed, subscriber)
        )

    def _on_subscribed(self, subscriber, response):
        '''Handle acknowledgement of subscription.'''
        if response.get('success') is False:
            self.logger.warning(
                'Server failed to subscribe subscriber {0}: {1}'
                .format(subscriber.metadata['id'], response.get('message'))
            )

    def unsubscribe(self, subscriber_identifier):
        '''Unsubscribe subscriber with *subscriber_identifier*.

        .. note::

            If the server is not reachable then it won't be notified of the
            unsubscription. However, the subscriber will be removed locally
            regardless.

        '''
        subscriber = self.get_subscriber_by_identifier(subscriber_identifier)

        if subscriber is None:
            raise ftrack.exception.NotFoundError(
                'Cannot unsubscribe missing subscriber with identifier {0}'
                .format(subscriber_identifier)
            )

        self._subscribers.pop(self._subscribers.index(subscriber))

        # Notify the server if possible.
        unsubscribe_event = ftrack.event.base.Event(
            topic='ftrack.meta.unsubscribe',
            data=dict(subscriber=subscriber.metadata)
        )

        try:
            self._publish(
                unsubscribe_event,
                callback=functools.partial(self._on_unsubscribed, subscriber)
            )
        except ftrack.exception.EventHubConnectionError:
            self.logger.debug(
                'Failed to notify server to unsubscribe subscriber {0} as '
                'server not currently reachable.'
                .format(subscriber.metadata['id'])
            )

    def _on_unsubscribed(self, subscriber, response):
        '''Handle acknowledgement of unsubscribing *subscriber*.'''
        if response.get('success') is not True:
            self.logger.warning(
                'Server failed to unsubscribe subscriber {0}: {1}'
                .format(subscriber.metadata['id'], response.get('message'))
            )

    def _prepare_event(self, event):
        '''Prepare *event* for sending.'''
        event['source'].setdefault('id', self.id)
        event['source'].setdefault('user', {
            'username': getpass.getuser()
        })

    def _prepare_reply_event(self, event, source_event, source=None):
        '''Prepare *event* as a reply to another *source_event*.

        Modify *event*, setting appropriate values to target event correctly as
        a reply.

        '''
        event['target'] = 'id={0}'.format(source_event['source']['id'])
        event['in_reply_to_event'] = source_event['id']
        if source is not None:
            event['source'] = source

    def publish(
        self, event, synchronous=False, on_reply=None, on_error='raise'
    ):
        '''Publish *event*.

        If *synchronous* is specified as True then this method will wait and
        return a list of results from any called callbacks.

        .. note::

            Currently, if synchronous is True then only locally registered
            callbacks will be called and no event will be sent to the server.
            This may change in future.

        *on_reply* is an optional callable to call with any reply event that is
        received in response to the published *event*.

        .. note::

            Will not be called when *synchronous* is True.

        If *on_error* is set to 'ignore' then errors raised during publish of
        event will be caught by this method and ignored.

        '''
        try:
            return self._publish(
                event, synchronous=synchronous, on_reply=on_reply
            )
        except Exception:
            if on_error == 'ignore':
                pass
            else:
                raise

    def publish_reply(self, source_event, data, source=None):
        '''Publish a reply event to *source_event* with supplied *data*.

        If *source* is specified it will be used for the source value of the
        sent event.

        '''
        reply_event = ftrack.event.base.Event(
            'ftrack.meta.reply',
            data=data
        )
        self._prepare_reply_event(reply_event, source_event, source=source)
        self.publish(reply_event)

    def _publish(self, event, synchronous=False, callback=None, on_reply=None):
        '''Publish *event*.

        If *synchronous* is specified as True then this method will wait and
        return a list of results from any called callbacks.

        .. note::

            Currently, if synchronous is True then only locally registered
            callbacks will be called and no event will be sent to the server.
            This may change in future.

        A *callback* can also be specified. This callback will be called once
        the server acknowledges receipt of the sent event. A default callback
        that checks for errors from the server will be used if not specified.

        *on_reply* is an optional callable to call with any reply event that is
        received in response to the published *event*. Note that there is no
        guarantee that a reply will be sent.

        Raise :exc:`ftrack.exception.EventHubConnectionError` if not currently
        connected.

        '''
        # Prepare event adding any relevant additional information.
        self._prepare_event(event)

        if synchronous:
            # Bypass emitting event to server and instead call locally
            # registered handlers directly, collecting and returning results.
            return self._handle(event, synchronous=synchronous)

        if not self.connected:
            raise ftrack.exception.EventHubConnectionError(
                'Cannot publish event asynchronously as not connected to '
                'server.'
            )

        # Use standard callback if none specified.
        if callback is None:
            callback = functools.partial(self._on_published, event)

        # Emit event to central server for asynchronous processing.
        try:
            # Register on reply callback if specified.
            if on_reply is not None:
                # TODO: Add a timeout or some other approach to avoid growing
                # endlessly for events that never receive replies.
                self._reply_callbacks[event['id']] = on_reply

            try:
                self._emit_event_packet(
                    self._event_namespace, event, callback=callback
                )
            except ftrack.exception.EventHubConnectionError:
                # Connection may have dropped temporarily. Wait a few moments to
                # see if background thread reconnects automatically.
                time.sleep(15)

                self._emit_event_packet(
                    self._event_namespace, event, callback=callback
                )
            except:
                raise

        except Exception:
            # Failure to send event should not cause caller to fail.
            self.logger.exception('Error sending event {0}.'.format(event))

    def _on_published(self, event, response):
        '''Handle acknowledgement of published event.'''
        if response.get('success', False) is False:
            self.logger.error(
                'Server responded with error while publishing event {0}. '
                'Error was: {1}'
                .format(event, response.get('message'))
            )

    def _handle(self, event, synchronous=False):
        '''Handle *event*.

        If *synchronous* is True, do not send any automatic reply events.

        '''
        # Sort by priority, lower is higher.
        # TODO: Use a sorted list to avoid sorting each time in order to improve
        # performance.
        subscribers = sorted(
            self._subscribers, key=operator.attrgetter('priority')
        )

        results = []

        target = event.get('target', None)
        target_expression = None
        if target:
            try:
                target_expression = self._expression_parser.parse(target)
            except Exception:
                self.logger.exception(
                    'Cannot handle event as failed to parse event target '
                    'information: {0}'.format(event)
                )
                return

        for subscriber in subscribers:
            # Check if event is targeted to the subscriber.
            if (
                target_expression is not None
                and not target_expression.match(subscriber.metadata)
            ):
                continue

            # Check if subscriber interested in the event.
            if not subscriber.interested_in(event):
                continue

            response = None

            try:
                response = subscriber.callback(event)
                results.append(response)
            except Exception:
                self.logger.exception(
                    'Error calling subscriber {0} for event {1}.'
                    .format(subscriber, event)
                )

            # Automatically publish a non None response as a reply when not in
            # synchronous mode.
            if not synchronous and response is not None:

                try:
                    self.publish_reply(
                        event, data=response, source=subscriber.metadata
                    )

                except Exception:
                    self.logger.exception(
                        'Error publishing response {0} from subscriber {1} '
                        'for event {2}.'
                        .format(response, subscriber, event)
                    )

            # Check whether to continue processing topic event.
            if event.is_stopped():
                self.logger.debug(
                    'Subscriber {0} stopped event {1}. Will not process '
                    'subsequent subscriber callbacks for this event.'
                    .format(subscriber, event)
                )
                break

        return results

    def _handle_reply(self, event):
        '''Handle reply *event*, passing it to any registered callback.'''
        callback = self._reply_callbacks.pop(event['in_reply_to_event'], None)
        if callback is not None:
            callback(event)

    def subscription(self, subscription, callback, subscriber=None,
                     priority=100):
        '''Return context manager with *callback* subscribed to *subscription*.

        The subscribed callback will be automatically unsubscribed on exit
        of the context manager.

        '''
        return _SubscriptionContext(
            self, subscription, callback, subscriber=subscriber,
            priority=priority,
        )

    # Socket.IO interface.
    #

    def _get_socket_io_session(self):
        '''Connect to server and retrieve session information.'''
        socket_io_url = '{0}://{1}:{2}/socket.io/1/'.format(*self.server)
        try:
            response = requests.get(
                socket_io_url,
                verify=False  # Allow self-signed SSL.
            )
        except requests.exceptions.Timeout as error:
            raise ftrack.exception.EventHubConnectionError(
                'Timed out connecting to server: {0}.'.format(error)
            )
        except requests.exceptions.SSLError as error:
            raise ftrack.exception.EventHubConnectionError(
                'Failed to negotiate SSL with server: {0}.'.format(error)
            )
        except requests.exceptions.ConnectionError as error:
            raise ftrack.exception.EventHubConnectionError(
                'Failed to connect to server: {0}.'.format(error)
            )
        else:
            status = response.status_code
            if status != 200:
                raise ftrack.exception.EventHubConnectionError(
                    'Received unexpected status code {0}.'.format(status)
                )

        # Parse result and return session information.
        parts = response.text.split(':')
        return SocketIoSession(
            parts[0],
            parts[1],
            parts[3].split(',')
        )

    def _add_packet_callback(self, callback):
        '''Store callback against a new unique packet ID.

        Return the unique packet ID.

        '''
        with self._lock:
            self._unique_packet_id += 1
            unique_identifier = self._unique_packet_id

        self._packet_callbacks[unique_identifier] = callback

        return '{0}+'.format(unique_identifier)

    def _pop_packet_callback(self, packet_identifier):
        '''Pop and return callback for *packet_identifier*.'''
        return self._packet_callbacks.pop(packet_identifier)

    def _emit_event_packet(self, event, args, callback):
        '''Send event packet.'''
        data = self._encode(
            dict(name=event, args=[args])
        )
        self._send_packet(
            self._code_name_mapping['event'], data=data, callback=callback
        )

    def _acknowledge_packet(self, packet_identifier, *args):
        '''Send acknowledgement of packet with *packet_identifier*.'''
        packet_identifier = packet_identifier.rstrip('+')
        data = str(packet_identifier)
        if args:
            data += '+{1}'.format(self._encode(args))

        self._send_packet(self._code_name_mapping['acknowledge'], data=data)

    def _send_packet(self, code, data='', callback=None):
        '''Send packet via connection.'''
        path = ''
        packet_identifier = (
            self._add_packet_callback(callback) if callback else ''
        )
        packet_parts = (str(code), packet_identifier, path, data)
        packet = ':'.join(packet_parts)

        try:
            self._connection.send(packet)
            self.logger.debug('Sent packet: {0}'.format(packet))
        except socket.error as error:
            raise ftrack.exception.EventHubConnectionError(
                'Failed to send packet: {0}'.format(error)
            )

    def _receive_packet(self):
        '''Receive and return packet via connection.'''
        try:
            packet = self._connection.recv()
        except Exception as error:
            raise ftrack.exception.EventHubConnectionError(
                'Error receiving packet: {0}'.format(error)
            )

        try:
            parts = packet.split(':', 3)
        except AttributeError:
            raise ftrack.exception.EventHubPacketError(
                'Received invalid packet {0}'.format(packet)
            )

        code, packet_identifier, path, data = None, None, None, None

        count = len(parts)
        if count == 4:
            code, packet_identifier, path, data = parts
        elif count == 3:
            code, packet_identifier, path = parts
        elif count == 1:
            code = parts[0]
        else:
            raise ftrack.exception.EventHubPacketError(
                'Received invalid packet {0}'.format(packet)
            )

        self.logger.debug('Received packet: {0}'.format(packet))
        return code, packet_identifier, path, data

    def _handle_packet(self, code, packet_identifier, path, data):
        '''Handle packet received from server.'''
        code_name = self._code_name_mapping[code]

        if code_name == 'connect':
            self.logger.debug('Connected to event server.')
            event = ftrack.event.base.Event('ftrack.meta.connected')
            self._event_queue.put(event)

        elif code_name == 'disconnect':
            self.logger.debug('Disconnected from event server.')
            if not self._intentional_disconnect:
                self.logger.debug(
                    'Disconnected unexpectedly. Attempting to reconnect.'
                )
                try:
                    self.reconnect(
                        attempts=self._auto_reconnect_attempts,
                        delay=self._auto_reconnect_delay
                    )
                except ftrack.exception.EventHubConnectionError:
                    self.logger.debug('Failed to reconnect automatically.')
                else:
                    self.logger.debug('Reconnected successfully.')

            if not self.connected:
                event = ftrack.event.base.Event('ftrack.meta.disconnected')
                self._event_queue.put(event)

        elif code_name == 'heartbeat':
            # Reply with heartbeat.
            self._send_packet(self._code_name_mapping['heartbeat'])

        elif code_name == 'message':
            self.logger.debug('Message received: {0}'.format(data))

        elif code_name == 'event':
            payload = self._decode(data)
            args = payload.get('args', [])

            if len(args) == 1:
                event_payload = args[0]
                if isinstance(event_payload, collections.Mapping):
                    try:
                        event = ftrack.event.base.Event(**event_payload)
                    except Exception:
                        self.logger.exception(
                            'Failed to convert payload into event: {0}'
                            .format(event_payload)
                        )
                        return

                    self._event_queue.put(event)

        elif code_name == 'acknowledge':
            parts = data.split('+', 1)
            acknowledged_packet_identifier = int(parts[0])
            args = []
            if len(parts) == 2:
                args = self._decode(parts[1])

            try:
                callback = self._pop_packet_callback(
                    acknowledged_packet_identifier
                )
            except KeyError:
                pass
            else:
                callback(*args)

        elif code_name == 'error':
            self.logger.error('Event server reported error: {0}.'.format(data))

        else:
            self.logger.debug('{0}: {1}'.format(code_name, data))

    def _encode(self, data):
        '''Return *data* encoded as JSON formatted string.'''
        return json.dumps(
            data,
            default=self._encode_default,
            ensure_ascii=False
        )

    def _encode_default(self, item):
        '''Return JSON encodable version of *item*.'''
        if isinstance(item, collections.Mapping):
            if 'in_reply_to_event' in item:
                item['inReplyToEvent'] = item.pop('in_reply_to_event')

        return item

    def _decode(self, string):
        '''Return decoded JSON *string* as Python object.'''
        return json.loads(string, object_hook=self._decode_object_hook)

    def _decode_object_hook(self, item):
        '''Return *item* transformed.'''
        if isinstance(item, collections.Mapping):
            if 'inReplyToEvent' in item:
                item['in_reply_to_event'] = item.pop('inReplyToEvent')

        return item


class _SubscriptionContext(object):
    '''Context manager for a one-off subscription.'''

    def __init__(self, hub, subscription, callback, subscriber, priority):
        '''Initialise context.'''
        self._hub = hub
        self._subscription = subscription
        self._callback = callback
        self._subscriber = subscriber
        self._priority = priority
        self._subscriberIdentifier = None

    def __enter__(self):
        '''Enter context subscribing callback to topic.'''
        self._subscriberIdentifier = self._hub.subscribe(
            self._subscription, self._callback, subscriber=self._subscriber,
            priority=self._priority
        )

    def __exit__(self, exception_type, exception_value, traceback):
        '''Exit context unsubscribing callback from topic.'''
        self._hub.unsubscribe(self._subscriberIdentifier)


class _ProcessorThread(threading.Thread):
    '''Process messages from server.'''

    daemon = True

    def __init__(self, client):
        '''Initialise thread with Socket.IO *client* instance.'''
        super(_ProcessorThread, self).__init__()
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.client = client
        self.done = threading.Event()

    def run(self):
        '''Perform work in thread.'''
        while not self.done.is_set():
            try:
                code, packet_identifier, path, data = self.client._receive_packet()
                self.client._handle_packet(code, packet_identifier, path, data)

            except ftrack.exception.EventHubPacketError as error:
                self.logger.debug(
                    'Ignoring invalid packet: {0}'.format(error)
                )
                continue

            except ftrack.exception.EventHubConnectionError:
                self.cancel()

                # Fake a disconnection event in order to trigger reconnection
                # when necessary.
                self.client._handle_packet('0', '', '', '')

                break

            except Exception as error:
                self.logger.debug(
                    'Aborting processor thread: {0}'.format(error)
                )
                self.cancel()
                break

    def cancel(self):
        '''Cancel work as soon as possible.'''
        self.done.set()
