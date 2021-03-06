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

ports = ['61/Module1/Port1', '61/Module2/Port2']
ports = ['207/Module1/Port1', '207/Module2/Port2']

controller = 'localhost'
port = '11009'

controller = '192.168.65.73'
port = '443'
ports = ['6553/Module1/Port2', '6553/Module1/Port1']

config='test_config_ngpf.ixncfg'

attributes = [AttributeNameValue('Controller Address', controller),
              AttributeNameValue('Controller TCP Port', port),
              AttributeNameValue('User', 'admin'),
              AttributeNameValue('Password', 'admin')]


class TestIxNetworkControllerShell(unittest.TestCase):

    def setUp(self):
        self.session = create_session_from_cloudshell_config()
        self.context = create_command_context(self.session, ports, 'IxNetwork Controller', attributes)

    def tearDown(self):
        reservation_id = self.context.reservation.reservation_id
        self.session.EndReservation(reservation_id)
        while self.session.GetReservationDetails(reservation_id).ReservationDescription.Status != 'Completed':
            time.sleep(1)
        self.session.DeleteReservation(reservation_id)

    def test_session_id(self):
        session_id = self.session.ExecuteCommand(self.context.reservation.reservation_id, 'IxNetwork Controller',
                                                 'Service', 'get_session_id')
        print('session_id = {}'.format(session_id.Output[1:-1]))
        root_obj = '{}ixnetwork'.format(session_id.Output[1:-1])
        print('root_obj = {}'.format(root_obj))

        globals = self.session.ExecuteCommand(self.context.reservation.reservation_id, 'IxNetwork Controller',
                                              'Service', 'get_children',
                                              [InputNameValue('obj_ref', root_obj),
                                               InputNameValue('child_type', 'globals')])
        print('globals = {}'.format(globals.Output))
        globals_obj = json.loads(globals.Output)[0]
        prefs = self.session.ExecuteCommand(self.context.reservation.reservation_id, 'IxNetwork Controller',
                                            'Service', 'get_children',
                                            [InputNameValue('obj_ref', globals_obj),
                                             InputNameValue('child_type', 'preferences')])
        print('preferences = {}'.format(prefs.Output))
        prefs_obj = json.loads(prefs.Output)[0]
        prefs_attrs = self.session.ExecuteCommand(self.context.reservation.reservation_id, 'IxNetwork Controller',
                                                  'Service', 'get_attributes',
                                                  [InputNameValue('obj_ref', prefs_obj)])
        print('preferences attributes = {}'.format(prefs_attrs.Output))

        self.session.ExecuteCommand(self.context.reservation.reservation_id, 'IxNetwork Controller',
                                    'Service', 'set_attribute',
                                    [InputNameValue('obj_ref', prefs_obj),
                                     InputNameValue('attr_name', 'connectPortsOnLoadConfig'),
                                     InputNameValue('attr_value', 'True')])
        prefs_attrs = self.session.ExecuteCommand(self.context.reservation.reservation_id, 'IxNetwork Controller',
                                                  'Service', 'get_attributes',
                                                  [InputNameValue('obj_ref', prefs_obj)])
        print('preferences attributes = {}'.format(prefs_attrs.Output))

    def test_load_config(self):
        self._load_config(path.join(path.dirname(__file__), config))

    def test_run_traffic(self):
        self._load_config(path.join(path.dirname(__file__), config))
        self.session.ExecuteCommand(self.context.reservation.reservation_id, 'IxNetwork Controller', 'Service',
                                    'send_arp')
        self.session.ExecuteCommand(self.context.reservation.reservation_id, 'IxNetwork Controller', 'Service',
                                    'start_protocols')
        self.session.ExecuteCommand(self.context.reservation.reservation_id, 'IxNetwork Controller', 'Service',
                                    'start_traffic', [InputNameValue('blocking', 'True')])
        self.session.ExecuteCommand(self.context.reservation.reservation_id, 'IxNetwork Controller', 'Service',
                                    'stop_traffic')
        stats = self.session.ExecuteCommand(self.context.reservation.reservation_id, 'IxNetwork Controller', 'Service',
                                            'get_statistics', [InputNameValue('view_name', 'Port Statistics'),
                                                               InputNameValue('output_type', 'JSON')])
        assert(int(json.loads(stats.Output)['Port 1']['Frames Tx.']) >= 2000)

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
