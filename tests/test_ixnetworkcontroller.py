#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import unittest

from cloudshell.shell.core.context import (ResourceCommandContext, ResourceContextDetails, ReservationContextDetails,
                                           ConnectivityContext)
from cloudshell.api.cloudshell_api import CloudShellAPISession
from src.driver import IxNetworkControllerDriver
from src.ixn_handler import get_reservation_ports

controller = 'localhost'
port = ''
install_path = 'C:/Program Files (x86)/Ixia/IxNetwork/8.20-EA'


def create_context(session):
    context = ResourceCommandContext()

    context.connectivity = ConnectivityContext()
    context.connectivity.server_address = 'localhost'
    context.connectivity.admin_auth_token = session.token_id

    response = session.CreateImmediateTopologyReservation('ixn unittest', 'admin', 60, False, False, 0, 'ixn test',
                                                          [], [], [])

    context.resource = ResourceContextDetails()
    context.resource.name = 'IxNetwork Controller'
    context.resource.attributes = {'Client Install Path': install_path,
                                   'Controller Address': controller,
                                   'Controller TCP Port': port}

    context.reservation = ReservationContextDetails()
    context.reservation.reservation_id = response.Reservation.Id
    context.reservation.owner_user = response.Reservation.Owner
    context.reservation.domain = response.Reservation.DomainName

    return context


class TestIxNetworkControllerDriver(unittest.TestCase):

    def setUp(self):
        self.session = CloudShellAPISession('localhost', 'admin', 'admin', 'Global')
        self.context = create_context(self.session)
        self.driver = IxNetworkControllerDriver()
        self.driver.initialize(self.context)

    def tearDown(self):
        self.driver.cleanup()
        self.session.EndReservation(self.context.reservation.reservation_id)
        self.session.TerminateReservation(self.context.reservation.reservation_id)

    def test_init(self):
        pass

    def test_load_config(self):
        reservation_ports = get_reservation_ports(self.session, self.context.reservation.reservation_id)
        self.session.SetAttributeValue(reservation_ports[0].Name, 'Logical Name', 'Port 1')
        self.session.SetAttributeValue(reservation_ports[1].Name, 'Logical Name', ' Port 2 ')
        self.driver.load_config(self.context, 'test_config.ixncfg')

    def test_run_traffic(self):
        self.test_load_config()
        self.driver.send_arp(self.context)
        self.driver.start_traffic(self.context, True)
        stats = self.driver.get_statistics(self.context, 'Port Statistics', 'json')
        print stats
        assert(int(stats['Port 1']['Frames Tx.']) == 1600)
        stats = self.driver.get_statistics(self.context, 'Port Statistics', 'csv')
        print stats

    def negative_tests(self):
        reservation_ports = get_reservation_ports(self.session, self.context.reservation.reservation_id)
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

if __name__ == '__main__':
    sys.exit(unittest.main())
