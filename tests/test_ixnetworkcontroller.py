#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import unittest

from cloudshell.api.cloudshell_api import CloudShellAPISession

from driver import IxNetworkControllerDriver
import tg_helper

controller = 'localhost'
port = ''
client_install_path = 'C:/Program Files (x86)/Ixia/IxNetwork/8.01-GA'


class TestIxNetworkControllerDriver(unittest.TestCase):

    def setUp(self):
        self.session = CloudShellAPISession('localhost', 'admin', 'admin', 'Global')
        self.context = tg_helper.create_context(self.session, 'ixn test', 'IxNetwork Controller', client_install_path)
        self.driver = IxNetworkControllerDriver()
        self.driver.initialize(self.context)

    def tearDown(self):
        self.driver.cleanup()
        self.session.EndReservation(self.context.reservation.reservation_id)
        self.session.TerminateReservation(self.context.reservation.reservation_id)

    def test_init(self):
        pass

    def test_load_config(self):
        reservation_ports = tg_helper.get_reservation_ports(self.session, self.context.reservation.reservation_id)
        self.session.SetAttributeValue(reservation_ports[0].Name, 'Logical Name', 'Port 1')
        self.session.SetAttributeValue(reservation_ports[1].Name, 'Logical Name', 'Port 2')
        self.driver.load_config(self.context, 'test_config.ixncfg')

    def test_run_traffic(self):
        self.test_load_config()
        self.driver.send_arp(self.context)
        self.driver.start_traffic(self.context, 'True')
        stats = self.driver.get_statistics(self.context, 'Port Statistics', 'JSON')
        print stats
        assert(int(stats['Port 1']['Frames Tx.']) == 1600)
        stats = self.driver.get_statistics(self.context, 'Port Statistics', 'csv')
        print stats

    def negative_tests(self):
        reservation_ports = tg_helper.get_reservation_ports(self.session, self.context.reservation.reservation_id)
        assert(len(reservation_ports) == 2)
        self.session.SetAttributeValue(reservation_ports[0].Name, 'Logical Name', 'Port 1')
        self.session.SetAttributeValue(reservation_ports[1].Name, 'Logical Name', '')
        self.assertRaises(Exception, self.driver.load_config, self.context, 'test_config.ixncfg')
        self.session.SetAttributeValue(reservation_ports[1].Name, 'Logical Name', 'Port 1')
        self.assertRaises(Exception, self.driver.load_config, self.context, 'test_config.ixncfg')
        self.session.SetAttributeValue(reservation_ports[1].Name, 'Logical Name', 'Port x')
        self.assertRaises(Exception, self.driver.load_config, self.context, 'test_config.ixncfg')
        # cleanup
        self.session.SetAttributeValue(reservation_ports[1].Name, 'Logical Name', 'Port 2')

    def test_run_quick_test(self):
        reservation_ports = tg_helper.get_reservation_ports(self.session, self.context.reservation.reservation_id)
        self.session.SetAttributeValue(reservation_ports[0].Name, 'Logical Name', 'Port 1')
        self.session.SetAttributeValue(reservation_ports[1].Name, 'Logical Name', 'Port 2')
        self.driver.load_config(self.context, 'quick_tests.ixncfg')
        print self.driver.run_quick_test(self.context, 'QuickTest3')

if __name__ == '__main__':
    sys.exit(unittest.main())
