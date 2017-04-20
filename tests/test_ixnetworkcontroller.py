#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import unittest

from cloudshell.shell.core.context import (ResourceCommandContext, ResourceContextDetails, ReservationContextDetails,
                                           ConnectivityContext)
from cloudshell.api.cloudshell_api import CloudShellAPISession
from src.driver import IxiaControllerDriver

controller = 'localhost'
port = ''
install_path = 'C:/Program Files (x86)/Ixia/IxNetwork/8.01-GA'


def create_context(session):
    context = ResourceCommandContext()

    context.connectivity = ConnectivityContext()
    context.connectivity.server_address = 'localhost'
    context.connectivity.admin_auth_token = session.token_id

    response = session.CreateImmediateTopologyReservation('ixn unittest', 'admin', 60, False, False, 0, 'ixn test',
                                                          [], [], [])

    context.resource = ResourceContextDetails()
    context.resource.name = 'IxNetwork Controller'
    context.resource.address = controller
    context.resource.attributes = {'Client Install Path': install_path,
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
        self.driver = IxiaControllerDriver()
        self.driver.initialize(self.context)

    def tearDown(self):
        self.driver.cleanup()
        self.session.EndReservation(self.context.reservation.reservation_id)
        self.session.TerminateReservation(self.context.reservation.reservation_id)

    def test_init(self):
        pass

    def test_load_config(self):
        self.driver.load_config(self.context, 'test_config.ixncfg')

if __name__ == '__main__':
    sys.exit(unittest.main())
