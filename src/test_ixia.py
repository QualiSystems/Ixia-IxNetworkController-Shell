#!/usr/bin/python
# -*- coding: utf-8 -*-
from cloudshell.shell.core.context import ResourceCommandContext, ResourceContextDetails, ReservationContextDetails,ConnectivityContext
from driver import IxiaControllerDriver
import thread



def create_context():
    context = ResourceCommandContext()
    context.resource = ResourceContextDetails()
    context.resource.name = 'Ixia Controller'
    context.reservation = ReservationContextDetails()
    context.reservation.reservation_id = '0a2bf55f-cf68-4a92-8bfd-1bd60d7d1202'
    context.reservation.owner_user = 'admin'
    context.reservation.owner_email = 'fake@qualisystems.com'
    context.reservation.environment_path ='config1'
    context.reservation.environment_name = 'config1'
    context.reservation.domain = 'Global'
    context.resource.attributes = {}
    context.resource.attributes['Client Install Path'] = 'C:/Program Files (x86)/Ixia/IxNetwork/8.01-GA'
    context.resource.address = 'localhost'
    return context

if __name__ == '__main__':

    context = create_context()
    driver = IxiaControllerDriver()

    driver.initialize(context)


    response = driver.load_config(context,'configs/basic_config.rxf')

    response = driver.send_arp(context)

    driver.get_statistics(context,'Port Statistics',"json")

    response = driver.start_devices(context)

    driver.start_traffic(context,"False")

    driver.stop_traffic(context)


