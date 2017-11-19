#!/usr/bin/python
# -*- coding: utf-8 -*-

from os import path
import sys
import unittest
import logging
import time

from cloudshell.shell.core.context import (ResourceCommandContext, ConnectivityContext, ReservationContextDetails,
                                           ResourceContextDetails)
from cloudshell.api.cloudshell_api import AttributeNameValue
from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext

from cloudshell.traffic.tg_helper import get_reservation_ports
from shellfoundry.releasetools.test_helper import create_session_from_cloudshell_config

from src.driver import IxNetworkControllerDriver

controller = 'localhost'
port = ''
client_install_path = 'C:/Program Files (x86)/Ixia/IxNetwork/8.01-GA'
controller_address = 'localhost'
controller_port = 8009

environment = 'ixn test'


class TestIxNetworkControllerDriver(unittest.TestCase):

    def setUp(self):
        self.session = create_session_from_cloudshell_config()

        self.reservation = self.session.CreateImmediateReservation(reservationName='ixn shell regression tests',
                                                                   owner='admin',
                                                                   durationInMinutes=60)
        reservation_id = self.reservation.Reservation.Id
        resources = ['Ixia Chassis Israel/Module2/Port1',
                     'Ixia Chassis Israel/Module2/Port2']
        self.session.AddResourcesToReservation(reservationId=reservation_id,
                                               resourcesFullPath=resources)
        attributes = [AttributeNameValue('Client Install Path', client_install_path),
                      AttributeNameValue('Controller Address', controller_address),
                      AttributeNameValue('Controller TCP Port', controller_port)]
        self.session.AddServiceToReservation(reservationId=reservation_id,
                                             serviceName='IxNetwork Controller',
                                             alias='IxNetwork Controller',
                                             attributes=attributes)
        service = self.session.GetReservationDetails(reservation_id).ReservationDescription.Services[0]
        attributes = {}
        for attribute in service.Attributes:
            attributes[attribute.Name] = attribute.Value

        self.context = ResourceCommandContext()

        self.context.connectivity = ConnectivityContext()
        self.context.connectivity.server_address = 'localhost'
        self.context.connectivity.admin_auth_token = self.session.token_id
        self.context.connectivity.cloudshell_api_scheme = CloudShellSessionContext.DEFAULT_API_SCHEME

        self.context.reservation = ReservationContextDetails()
        self.context.reservation.reservation_id = reservation_id
        self.context.reservation.owner_user = self.reservation.Reservation.Owner
        self.context.reservation.domain = self.reservation.Reservation.DomainName

        self.context.resource = ResourceContextDetails()
        self.context.resource.name = service.ServiceName
        self.context.resource.attributes = attributes

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

    def test_run_traffic(self):
        self._load_config(path.join(path.dirname(__file__), 'test_config.ixncfg'))
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

    def test_run_quick_test(self):
        self._load_config(path.join(path.dirname(__file__), 'quick_tests.ixncfg'))
        print self.driver.run_quick_test(self.context, 'QuickTest3')

    def _load_config(self, config):
        reservation_ports = get_reservation_ports(self.session, self.reservation.Reservation.Id)
        self.session.SetAttributeValue(reservation_ports[0].Name, 'Logical Name', 'Port 1')
        self.session.SetAttributeValue(reservation_ports[1].Name, 'Logical Name', 'Port 2')
        self.driver.load_config(self.context, config)


if __name__ == '__main__':
    sys.exit(unittest.main())
