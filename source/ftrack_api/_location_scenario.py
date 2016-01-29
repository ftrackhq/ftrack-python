import logging
import json
import sys

import ftrack_api
import ftrack_api.structure.standard as _standard


class CentralizedLocationScenario(object):

    scenario_name = 'ftrack.centralized-storage'

    def __init__(self):
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

    @property
    def location_scenario(self):
        return self.session.query(
            'select value from Setting '
            'where name is "location_scenario" and group is "LOCATION"'
        ).one()

    @property
    def existing_centralized_storage_configuration(self):
        location_scenario = self.location_scenario

        try:
            configuration = json.loads(location_scenario['value'])
        except (ValueError, TypeError):
            return None

        if not isinstance(configuration, dict):
            return None

        if configuration.get('scenario') != self.scenario_name:
            return None

        return configuration.get('data', {})

    def _get_confirmation_text(self, configuration):
        configure_location = configuration.get('configure_location')
        select_location = configuration.get('select_location')
        select_mount_point = configuration.get('select_mount_point')

        if configure_location:
            location_text = unicode(
                'A new location will be created:\n\n'
                '* Label: {location_label}\n'
                '* Name: {location_name}\n'
                '* Description: {location_description}\n'
            ).format(**configure_location)
        else:
            location = self.session.get(
                'Location', select_location['location_id']
            )
            location_text = (
                u'You have choosen to use an existing location: {0}'.format(
                    location['label']
                )
            )

        structure_text = (
            'The *Standard* structure will be used.'
        )

        mount_points_text = (
            '* Linux: {linux}\n'
            '* OS X: {osx}\n'
            '* Windows: {windows}\n\n'
        ).format(
            linux=select_mount_point.get('linux_mount_point') or '*Not set*',
            osx=select_mount_point.get('osx_mount_point') or '*Not set*',
            windows=select_mount_point.get('windows_mount_point') or '*Not set*'
        )

        mount_points_not_set = []

        if not select_mount_point.get('linux_mount_point'):
            mount_points_not_set.append('Linux')

        if not select_mount_point.get('osx_mount_point'):
            mount_points_not_set.append('OS X')

        if not select_mount_point.get('windows_mount_point'):
            mount_points_not_set.append('Windows')

        if mount_points_not_set:
            mount_points_text += (
                'Please be aware that this location will not be working on '
                '{missing} because the mount points are not set up.'
            ).format(
                missing=' and '.join(mount_points_not_set)
            )

        text = (
            '#Confirm location setup#\n\n'
            'Almost there! Please take a moment to verify the settings you '
            'are about to save. You can always come back later and update the '
            'configuration.\n'
            '##Location##\n\n'
            '{location}\n'
            '##Structure##\n\n'
            '{structure}\n'
            '##Mount points##\n\n'
            '{mount_points}'
        ).format(
            location=location_text,
            structure=structure_text,
            mount_points=mount_points_text
        )

        return text

    def configure_scenario(self, event):

        steps = (
            'select_scenario',
            'select_location',
            'configure_location',
            'select_structure',
            'select_mount_point',
            'confirm_summary',
            'save_configuration'
        )

        values = event['data'].get('values', {})

        # Calculate previous step and the next.
        previous_step = values.get('step', 'select_scenario')
        next_step = steps[steps.index(previous_step) + 1]
        state = 'configuring'

        print 'Previous step', previous_step, ' Next step: ', next_step

        if 'configuration' in values:
            configuration = values.pop('configuration')
        else:
            configuration = {}

        if values:
            # Update configuration with values from the previous step.
            configuration[previous_step] = values

        if next_step == 'select_location':
            try:
                location_id = (
                    self.existing_centralized_storage_configuration['location_id']
                )
            except (KeyError, TypeError):
                location_id = None

            options = [{
                'label': 'Create new location',
                'value': 'create_new_location'
            }]
            for location in self.session.query(
                'select name, label, description from Location'
            ):
                if location['name'] not in (
                    'ftrack.origin', 'ftrack.unmanaged', 'ftrack.connect',
                    'ftrack.server', 'ftrack.review'
                ):
                    options.append({
                        'label': '{label} ({name})'.format(
                            label=location['label'], name=location['name']
                        ),
                        'description': location['description'],
                        'value': location['id']
                    })

            items = [{
                'type': 'label',
                'value': (
                    '#Select location#\n'
                    'Choose an already existing location or create a new to '
                    'represent your centralized storage.'
                )
            }, {
                'type': 'enumerator',
                'label': 'Location',
                'name': 'location_id',
                'value': location_id,
                'data': options
            }]

        if next_step == 'configure_location':

            if values.get('location_id') == 'create_new_location':
                # Add options to create a new location.
                items = [{
                    'type': 'label',
                    'value': (
                        '#Create location#\n'
                        'Here you will create a new location to be used '
                        'with your new Location scenario. For your '
                        'convencience we have already filled in some default '
                        'values. If this is the first time you configure a '
                        'location scenario in ftrack we recommend that you '
                        'stick with these settings.'
                    )
                }, {
                    'label': 'Label',
                    'name': 'location_label',
                    'value': 'Studio location',
                    'type': 'text'
                }, {
                    'label': 'Name',
                    'name': 'location_name',
                    'value': 'studio.central-location',
                    'type': 'text'
                }, {
                    'label': 'Description',
                    'name': 'location_description',
                    'value': (
                        'The studio central location where all components are '
                        'stored.'
                    ),
                    'type': 'text'
                }]

            else:
                # The user selected an existing location. Move on to next
                # step.
                next_step = 'select_structure'

        if next_step == 'select_structure':
            items = [
                {
                    'type': 'label',
                    'value': (
                        '#Select structure#\n'
                        'Select which structure to use with your location. The '
                        'structure is used to generate the filesystem path '
                        'for components that are added to this location.'
                    )
                },
                {
                    'type': 'enumerator',
                    'label': 'Structure',
                    'name': 'structure_id',
                    'value': 'standard',
                    'data': [{
                        'label': 'Standard',
                        'value': 'standard',
                        'description': (
                            'The Standard structure uses the names in your '
                            'project structure to determine the path.'
                        )
                    }]
                }
            ]

        if next_step == 'select_mount_point':
            try:
                mount_points = (
                    self.existing_centralized_storage_configuration['accessor']['mount_points']
                )
            except (KeyError, TypeError):
                mount_points = dict()

            items = [
                {
                    'value': (
                        '#Mount points#\n'
                        'Set mount points for your centralized storage '
                        'location. For the location to work as expected each '
                        'platform that you intend to use must have the '
                        'corresponding mount point set and the storage must '
                        'be accessible. If not set correctly files will not be '
                        'saved or read.'
                    ),
                    'type': 'label'
                }, {
                    'type': 'text',
                    'label': 'Linux',
                    'name': 'linux_mount_point',
                    'empty_text': 'E.g. /usr/mnt/MyStorage ...',
                    'value': mount_points.get('linux', '')
                }, {
                    'type': 'text',
                    'label': 'OS X',
                    'name': 'osx_mount_point',
                    'empty_text': 'E.g. /Volumes/MyStorage ...',
                    'value': mount_points.get('osx', '')
                }, {
                    'type': 'text',
                    'label': 'Windows',
                    'name': 'windows_mount_point',
                    'empty_text': 'E.g. \\\\MyStorage ...',
                    'value': mount_points.get('windows', '')
                }
            ]

        if next_step == 'confirm_summary':
            items = [{
                'type': 'label',
                'value': self._get_confirmation_text(configuration)
            }]
            state = 'confirm'

        if next_step == 'save_configuration':
            mount_points = configuration['select_mount_point']
            select_location = configuration['select_location']

            if select_location['location_id'] == 'create_new_location':
                configure_location = configuration['configure_location']
                location = self.session.create(
                    'Location',
                    {
                        'name': configure_location['location_name'],
                        'label': configure_location['location_label'],
                        'description': (
                            configure_location['location_description']
                        )
                    }
                )

            else:
                location = self.session.query(
                    'Location where id is "{0}"'.format(
                        select_location['location_id']
                    )
                ).one()

            setting_value = json.dumps({
                'scenario': self.scenario_name,
                'data': {
                    'location_id': location['id'],
                    'location_name': location['name'],
                    'accessor': {
                        'mount_points': {
                            'linux': mount_points['linux_mount_point'],
                            'osx': mount_points['osx_mount_point'],
                            'windows': mount_points['windows_mount_point']
                        }
                    }
                }
            })

            self.location_scenario['value'] = setting_value
            self.session.commit()

            items = [{
                'type': 'label',
                'value': (
                    '#Done!#\n'
                    'Your location scenario is now configured and ready '
                    'to use. Please restart Connect and other applications '
                    'to start using it.'
                )
            }]
            state = 'done'

        items.append({
            'type': 'hidden',
            'value': configuration,
            'name': 'configuration'
        })
        items.append({
            'type': 'hidden',
            'value': next_step,
            'name': 'step'
        })

        return {
            'items': items,
            'state': state
        }

    def discover_centralized_scenario(self, event):
        return {
            'id': 'centralized_scenario',
            'name': 'Centralized scenario',
            'description': 'A centralized location scenario'
        }

    def activate(self, event):
        location_scenario = event['data']['location_scenario']

        try:
            location_data = location_scenario['data']
            location_name = location_data['location_name']
            location_id = location_data['location_id']
            mount_points = location_data['accessor']['mount_points']

        except KeyError:
            error_message = (
                'Unable to read location scenario data.'
            )
            self.logger.error(error_message)
            raise ftrack_api.exception.LocationError(
                'Unable to configure location based on scenario.'
            )

        else:
            location = self.session.create(
                'Location',
                data=dict(
                    name=location_name,
                    id=location_id
                ),
                reconstructing=True
            )

            if sys.platform == 'darwin':
                prefix = mount_points['osx']
            elif sys.platform == 'linux2':
                prefix = mount_points['linux']
            elif sys.platform == 'windows':
                prefix = mount_points['windows']
            else:
                raise ftrack_api.exception.LocationError(
                    (
                        'Unable to find accessor prefix for platform {0}.'
                    ).format(sys.platform)
                )

            location.accessor = ftrack_api.accessor.disk.DiskAccessor(
                prefix=prefix
            )
            location.structure = _standard.StandardStructure()
            location.priority = 1

    def register(self, session):
        self.session = session

        session.event_hub.subscribe(
            'topic=ftrack.location-scenario.discover',
            self.discover_centralized_scenario
        )
        session.event_hub.subscribe(
            'topic=ftrack.location-scenario.configure',
            self.configure_scenario
        )
        session.event_hub.subscribe(
            'topic=ftrack.location-scenario.activate',
            self.activate
        )


def register(session):
    scenario = CentralizedLocationScenario()
    scenario.register(session)
