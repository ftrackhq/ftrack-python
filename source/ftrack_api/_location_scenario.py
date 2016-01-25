import logging
import json

logging.basicConfig(level=logging.DEBUG)


class CentralizedLocationScenario(object):

    scenario_name = 'ftrack.centralized-storage'

    @property
    def location_scenario(self):
        return self.session.query(
            'select value from Setting '
            'where name is "location_scenario" and group is "LOCATION"'
        ).one()

    def configure_scenario(self, event):
        values = event['data'].get('values', {})

        if 'linux_mount_point' not in values and 'configuration' not in values:
            description = (
                'Set mount points for your centralized storage location.'
            )
            location_scenario = json.loads(self.location_scenario['value'])

            mount_points = dict()

            if location_scenario['scenario'] == self.scenario_name:
                try:
                    mount_points = (
                        location_scenario['data']['accessor']['mount_points']
                    )
                except (KeyError, TypeError) as error:
                    pass

            return {
                'items': [{
                    'value': description,
                    'type': 'label'
                }, {
                    'type': 'text',
                    'label': 'Linux',
                    'name': 'linux_mount_point',
                    'value': mount_points.get('linux', '')
                }, {
                    'type': 'text',
                    'label': 'OS X',
                    'name': 'osx_mount_point',
                    'value': mount_points.get('osx', '')
                }, {
                    'type': 'text',
                    'label': 'Windows',
                    'name': 'windows_mount_point',
                    'value': mount_points.get('windows', '')
                }]
            }
        elif 'configuration' not in values:
            summary = unicode(
                'You will update the location scenario to use a Centralized '
                'location. Your mount points are: \n\n'
                '* Linux: {linux} \n'
                '* OS X: {osx}\n'
                '* Windows: {windows}\n\n'
                'Notice that the location will not work properly on platforms '
                'that doesn\'nt have a mount point filled in or accessible.'
            ).format(
                linux=values['linux_mount_point'],
                osx=values['osx_mount_point'],
                windows=values['windows_mount_point']
            )

            return {
                'summary': True,
                'items': [{
                    'type': 'label',
                    'value': summary
                }, {
                    'type': 'hidden',
                    'value': values,
                    'name': 'configuration'
                }]
            }
        else:
            configuration = values['configuration']
            self.location_scenario['value'] = json.dumps({
                'scenario': self.scenario_name,
                'data': {
                    'location_id': '',
                    'location_name': '',
                    'accessor': {
                        'mount_points': {
                            'linux': configuration['linux_mount_point'],
                            'osx': configuration['osx_mount_point'],
                            'windows': configuration['windows_mount_point']
                        }
                    }
                }
            })
            self.session.commit()

    def discover_centralized_scenario(self, event):
        return {
            'id': 'centralized_scenario',
            'name': 'Centralized scenario',
            'description': 'A centralized location scenario'
        }

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


def register(session):
    scenario = CentralizedLocationScenario()
    scenario.register(session)
