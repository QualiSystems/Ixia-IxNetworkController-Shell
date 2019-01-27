#!/usr/bin/python
# -*- coding: utf-8 -*-

from os import path
import sys
import unittest
import logging

from cloudshell.traffic.tg_helper import get_reservation_resources, set_family_attribute
from shellfoundry.releasetools.test_helper import create_session_from_cloudshell_config, create_command_context

from src.driver import IxNetworkControllerDriver

controller = '172.40.0.228'
port = '8008'

ports = ['IxVM 801/Module1/Port1', 'IxVM 801/Module1/Port2']
ports = ['ixia 2g/Module1/Port1', 'ixia 2g/Module2/Port2']
ports = ['217/Module1/Port2', '217/Module1/Port1']
ports = ['184/Module1/Port2', '184/Module1/Port1']
attributes = {'Controller Address': controller,
              'Controller TCP Port': port}


class TestIxNetworkControllerDriver(object):

    def setup(self):
        self.session = create_session_from_cloudshell_config()
        self.context = create_command_context(self.session, ports, 'IxNetwork Controller', attributes)
        self.driver = IxNetworkControllerDriver()
        self.driver.initialize(self.context)
        print self.driver.logger.handlers[0].baseFilename
        self.driver.logger.addHandler(logging.StreamHandler(sys.stdout))

    def teardown(self):
        self.driver.cleanup()
        self.session.EndReservation(self.context.reservation.reservation_id)

    def test_init(self):
        pass

    def test_load_config(self):
        reservation_ports = get_reservation_resources(self.session, self.context.reservation.reservation_id,
                                                      'Generic Traffic Generator Port',
                                                      'PerfectStorm Chassis Shell 2G.GenericTrafficGeneratorPort',
                                                      'Ixia Chassis Shell 2G.GenericTrafficGeneratorPort')
        set_family_attribute(self.session, reservation_ports[0], 'Logical Name', 'Port 1')
        set_family_attribute(self.session, reservation_ports[1], 'Logical Name', 'Port 2')
        self.driver.load_config(self.context, path.join(path.dirname(__file__), 'test_config_840.ixncfg'))

    def test_run_traffic(self):
        self.test_load_config()
        self.driver.send_arp(self.context)
        self.driver.start_traffic(self.context, 'False')
        self.driver.stop_traffic(self.context)
        stats = self.driver.get_statistics(self.context, 'Port Statistics', 'JSON')
        assert(int(stats['Port 1']['Frames Tx.']) <= 1600)
        self.driver.start_traffic(self.context, 'True')
        stats = self.driver.get_statistics(self.context, 'Port Statistics', 'JSON')
        assert(int(stats['Port 1']['Frames Tx.']) == 1600)
        stats = self.driver.get_statistics(self.context, 'Port Statistics', 'csv')
        print stats

    def negative_tests(self):
        reservation_ports = get_reservation_resources(self.session, self.context.reservation.reservation_id,
                                                      'Generic Traffic Generator Port',
                                                      'PerfectStorm Chassis Shell 2G.GenericTrafficGeneratorPort',
                                                      'Ixia Chassis Shell 2G.GenericTrafficGeneratorPort')
        assert(len(reservation_ports) == 2)
        set_family_attribute(self.session, reservation_ports[0], 'Logical Name', 'Port 1')
        set_family_attribute(self.session, reservation_ports[1], 'Logical Name', '')
        self.assertRaises(Exception, self.driver.load_config, self.context,
                          path.join(path.dirname(__file__), 'test_config_840.ixncfg'))
        set_family_attribute(self.session, reservation_ports[1], 'Logical Name', 'Port 1')
        self.assertRaises(Exception, self.driver.load_config, self.context,
                          path.join(path.dirname(__file__), 'test_config_840.ixncfg'))
        set_family_attribute(self.session, reservation_ports[1], 'Logical Name', 'Port x')
        self.assertRaises(Exception, self.driver.load_config, self.context,
                          path.join(path.dirname(__file__), 'test_config_840.ixncfg'))
        # cleanup
        set_family_attribute(self.session, reservation_ports[1], 'Logical Name', 'Port 2')

    def test_run_quick_test(self):
        reservation_ports = get_reservation_resources(self.session, self.context.reservation.reservation_id,
                                                      'Generic Traffic Generator Port',
                                                      'PerfectStorm Chassis Shell 2G.GenericTrafficGeneratorPort',
                                                      'Ixia Chassis Shell 2G.GenericTrafficGeneratorPort')
        set_family_attribute(self.session, reservation_ports[0], 'Logical Name', 'Port 1')
        set_family_attribute(self.session, reservation_ports[1], 'Logical Name', 'Port 2')
        self.driver.load_config(self.context, path.join(path.dirname(__file__), 'quick_tests_840.ixncfg'))
        print self.driver.run_quick_test(self.context, 'QuickTest3')


if __name__ == '__main__':
    sys.exit(unittest.main())
