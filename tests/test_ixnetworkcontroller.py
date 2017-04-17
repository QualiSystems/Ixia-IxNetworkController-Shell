#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import unittest

from cloudshell.shell.core.context import (ResourceCommandContext, ResourceContextDetails, ReservationContextDetails,
                                           ConnectivityContext)
from src.driver import IxiaControllerDriver

controller = 'NA'
port = ''
install_path = 'C:/Program Files (x86)/Ixia/IxNetwork/8.01-GA'

reservation_id = '87952f34-09a2-4011-838c-ea10a4a4740a'
admin_auth_token = ''


def create_context():
    context = ResourceCommandContext()

    context.connectivity = ConnectivityContext()
    context.connectivity.server_address = 'localhost'
    context.connectivity.admin_auth_token = admin_auth_token

    context.resource = ResourceContextDetails()
    context.resource.name = 'IxNetwork Controller'

    context.reservation = ReservationContextDetails()
    context.reservation.reservation_id = reservation_id
    context.reservation.owner_user = 'admin'
    context.reservation.owner_email = 'fake@qualisystems.com'
    context.reservation.environment_path = 'config1'
    context.reservation.environment_name = 'config1'
    context.reservation.domain = 'Global'

    context.resource.address = controller
    context.resource.attributes = {'Client Install Path': install_path,
                                   'Controller TCP Port': port}

    return context


class TestIxNetworkControllerDriver(unittest.TestCase):

    def setUp(self):
        self.context = create_context()
        self.driver = IxiaControllerDriver()
        self.driver.initialize(self.context)

    def tearDown(self):
        self.driver.cleanup()

    def test_init(self):
        pass

    def test_auto_load(self):
        self.driver.get_inventory(None)

    def test_load_config(self):
        self.driver.load_config(self.context, 'test_config.ixncfg')

if __name__ == '__main__':
    sys.exit(unittest.main())
