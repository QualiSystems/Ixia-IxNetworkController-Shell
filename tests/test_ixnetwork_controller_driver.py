#!/usr/bin/python
# -*- coding: utf-8 -*-

from os import path
import sys
import unittest
import logging
import time

from cloudshell.traffic.tg_helper import get_reservation_ports
from shellfoundry.releasetools.test_helper import create_session_from_cloudshell_config, create_command_context

from src.driver import IxNetworkControllerDriver

host = 'localhost'
controller = 'localhost'
port = ''
client_install_path = 'C:/Program Files (x86)/Ixia/IxNetwork/8.01-GA'
environment = 'Ixn Test'


class TestIxNetworkControllerDriver(unittest.TestCase):

    def setUp(self):
        self.session = create_session_from_cloudshell_config()
        self.context = create_command_context(host, self.session, environment, 'IxNetwork Controller',
                                              client_install_path)
        self.driver = IxNetworkControllerDriver()
        self.driver.initialize(self.context)
        print self.driver.logger.handlers[0].baseFilename
        self.driver.logger.addHandler(logging.StreamHandler(sys.stdout))

    def tearDown(self):
        self.driver.cleanup()
        self.session.EndReservation(self.context.reservation.reservation_id)
        time.sleep(16)
        self.session.DeleteReservation(self.context.reservation.reservation_id)

    def test_init(self):
        pass

    def test_load_config(self):
        reservation_ports = get_reservation_ports(self.session, self.context.reservation.reservation_id)
        self.session.SetAttributeValue(reservation_ports[0].Name, 'Logical Name', 'Port 1')
        self.session.SetAttributeValue(reservation_ports[1].Name, 'Logical Name', 'Port 2')
        self.driver.load_config(self.context, path.join(path.dirname(__file__), 'test_config.ixncfg'))

    def test_run_traffic(self):
        self.test_load_config()
        self.driver.send_arp(self.context)
        self.driver.start_protocols(self.context)
        self.driver.stop_protocols(self.context)
        self.driver.start_traffic(self.context, 'False')
        self.driver.stop_traffic(self.context)
        stats = self.driver.get_statistics(self.context, 'Port Statistics', 'JSON')
        assert(int(stats['Port 1']['Frames Tx.']) < 1600)
        self.driver.start_traffic(self.context, 'True')
        stats = self.driver.get_statistics(self.context, 'Port Statistics', 'JSON')
        assert(int(stats['Port 1']['Frames Tx.']) == 1600)
        stats = self.driver.get_statistics(self.context, 'Port Statistics', 'csv')
        print stats

    def negative_tests(self):
        reservation_ports = get_reservation_ports(self.session, self.context.reservation.reservation_id)
        assert(len(reservation_ports) == 2)
        self.session.SetAttributeValue(reservation_ports[0].Name, 'Logical Name', 'Port 1')
        self.session.SetAttributeValue(reservation_ports[1].Name, 'Logical Name', '')
        self.assertRaises(Exception, self.driver.load_config, self.context,
                          path.join(path.dirname(__file__), 'test_config.ixncfg'))
        self.session.SetAttributeValue(reservation_ports[1].Name, 'Logical Name', 'Port 1')
        self.assertRaises(Exception, self.driver.load_config, self.context,
                          path.join(path.dirname(__file__), 'test_config.ixncfg'))
        self.session.SetAttributeValue(reservation_ports[1].Name, 'Logical Name', 'Port x')
        self.assertRaises(Exception, self.driver.load_config, self.context,
                          path.join(path.dirname(__file__), 'test_config.ixncfg'))
        # cleanup
        self.session.SetAttributeValue(reservation_ports[1].Name, 'Logical Name', 'Port 2')

    def test_run_quick_test(self):
        reservation_ports = get_reservation_ports(self.session, self.context.reservation.reservation_id)
        self.session.SetAttributeValue(reservation_ports[0].Name, 'Logical Name', 'Port 1')
        self.session.SetAttributeValue(reservation_ports[1].Name, 'Logical Name', 'Port 2')
        self.driver.load_config(self.context, path.join(path.dirname(__file__), 'quick_tests.ixncfg'))
        print self.driver.run_quick_test(self.context, 'QuickTest3')


if __name__ == '__main__':
    sys.exit(unittest.main())
