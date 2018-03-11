#!/usr/bin/python
# -*- coding: utf-8 -*-

from os import path
import sys
import unittest
import time
import json

from cloudshell.api.cloudshell_api import AttributeNameValue, InputNameValue
from cloudshell.traffic.tg_helper import get_reservation_resources, set_family_attribute
from shellfoundry.releasetools.test_helper import create_session_from_cloudshell_config, create_command_context

# must be str
controller = '192.168.85.23'
port = '8008'

ports = ['ixia 2g/Module1/Port1', 'ixia 2g/Module2/Port2']
ports = ['IxVM 801/Module1/Port1', 'IxVM 801/Module1/Port2']
ports = ['217/Module1/Port1', '217/Module1/Port2']
attributes = [AttributeNameValue('Controller Address', controller),
              AttributeNameValue('Controller TCP Port', port)]


class TestIxNetworkControllerDriver(unittest.TestCase):

    def setUp(self):
        self.session = create_session_from_cloudshell_config()
        self.context = create_command_context(self.session, ports, 'IxNetwork Controller', attributes)

    def tearDown(self):
        reservation_id = self.context.reservation.reservation_id
        self.session.EndReservation(reservation_id)
        while self.session.GetReservationDetails(reservation_id).ReservationDescription.Status != 'Completed':
            time.sleep(1)
        self.session.DeleteReservation(reservation_id)

    def test_load_config(self):
        self._load_config(path.join(path.dirname(__file__), 'test_config_840.ixncfg'))

    def test_run_traffic(self):
        self._load_config(path.join(path.dirname(__file__), 'test_config_840.ixncfg'))
        self.session.ExecuteCommand(self.context.reservation.reservation_id, 'IxNetwork Controller', 'Service',
                                    'send_arp')
        self.session.ExecuteCommand(self.context.reservation.reservation_id, 'IxNetwork Controller', 'Service',
                                    'send_arp')
        self.session.ExecuteCommand(self.context.reservation.reservation_id, 'IxNetwork Controller', 'Service',
                                    'start_protocols')
        self.session.ExecuteCommand(self.context.reservation.reservation_id, 'IxNetwork Controller', 'Service',
                                    'stop_protocols')
        self.session.ExecuteCommand(self.context.reservation.reservation_id, 'IxNetwork Controller', 'Service',
                                    'start_traffic', [InputNameValue('blocking', 'True')])
        self.session.ExecuteCommand(self.context.reservation.reservation_id, 'IxNetwork Controller', 'Service',
                                    'stop_traffic')
        stats = self.session.ExecuteCommand(self.context.reservation.reservation_id, 'IxNetwork Controller', 'Service',
                                            'get_statistics', [InputNameValue('view_name', 'Port Statistics'),
                                                               InputNameValue('output_type', 'JSON')])
        assert(int(json.loads(stats.Output)['Port 1']['Frames Tx.']) >= 1600)

    def test_run_quick_test(self):
        self._load_config(path.join(path.dirname(__file__), 'quick_tests_840.ixncfg'))
        self.session.ExecuteCommand(self.context.reservation.reservation_id, 'IxNetwork Controller', 'Service',
                                    'run_quick_test', [InputNameValue('test', 'QuickTest3')])

    def _load_config(self, config):
        reservation_ports = get_reservation_resources(self.session, self.context.reservation.reservation_id,
                                                      'Generic Traffic Generator Port',
                                                      'PerfectStorm Chassis Shell 2G.GenericTrafficGeneratorPort',
                                                      'Ixia Chassis Shell 2G.GenericTrafficGeneratorPort')
        set_family_attribute(self.session, reservation_ports[0], 'Logical Name', 'Port 1')
        set_family_attribute(self.session, reservation_ports[1], 'Logical Name', 'Port 2')
        self.session.ExecuteCommand(self.context.reservation.reservation_id, 'IxNetwork Controller', 'Service',
                                    'load_config', [InputNameValue('ixn_config_file_name', config)])


if __name__ == '__main__':
    sys.exit(unittest.main())