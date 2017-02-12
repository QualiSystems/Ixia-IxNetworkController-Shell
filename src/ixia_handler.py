import logging
from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext
from cloudshell.shell.core.driver_context import AutoLoadDetails
from trafficgenerator.tgn_tcl import TgnTkMultithread
from ixnetwork.ixn_app import IxnApp
from ixnetwork.api.ixn_tcl import IxnTclWrapper
from ixnetwork.ixn_statistics_view import IxnStatisticsView


import re
import json
import csv
import io

import os


class IxiaHandler(object):

    def initialize(self, context):
        """
        :type context: cloudshell.shell.core.driver_context.InitCommandContext
        """
        curr_dir = os.getcwd()
        log_dir = curr_dir+'/Logs'
        log_file = 'Ixia_logger.log'
        client_install_path = context.resource.attributes['Client Install Path']
        logging.basicConfig(filename= log_file, level=logging.DEBUG)
        self.logger = logging.getLogger('root')
        self.logger.addHandler(logging.FileHandler(log_file))
        self.logger.setLevel('DEBUG')

        self.tcl_interp = TgnTkMultithread()
        self.tcl_interp.start()
        api_wrapper = IxnTclWrapper(self.logger, client_install_path, self.tcl_interp)

        self.ixn = IxnApp(self.logger, api_wrapper)

        address = context.resource.address
        if address.lower() in ('na', 'localhost'):
            address = None
        self.logger.info("connecting to address {}".format(address))
        self.ixn.connect()

    def tearDown(self):
        self.tcl_interp.stop()

    def get_inventory(self, context):
        """
        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """

        return AutoLoadDetails([], [])

    def get_api(self, context):
        """

        :param context:
        :return:
        """

        return CloudShellSessionContext(context).get_api()

    def load_config(self, context, stc_config_file_name, get_data_from_config=False):
        """
        :param str stc_config_file_name: full path to STC configuration file (tcc or xml)
        :param context: the context the command runs on
        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """

        self.ixn.load_config(stc_config_file_name)
        self.ports = self.ixn.root.get_ports()

        if get_data_from_config.lower() == 'false':
            reservation_id = context.reservation.reservation_id
            my_api = self.get_api(context)
            response = my_api.GetReservationDetails(reservationId=reservation_id)

            search_chassis = "Ixia Chassis"
            search_port = "Port"
            chassis_obj = None
            ports_obj = []

            for resource in response.ReservationDescription.Resources:
                if resource.ResourceModelName == search_chassis:
                    chassis_obj = resource
                if resource.ResourceFamilyName == search_port:
                    ports_obj.append(resource)

            ports_obj_dict = dict()
            for port in ports_obj:
                if (chassis_obj.FullAddress in port.FullAddress):
                    val = my_api.GetAttributeValue(resourceFullPath=port.Name, attributeName="Logical Name").Value
                    if val:
                        port.logic_name = val
                        ports_obj_dict[val.lower().strip()] = port
            if not ports_obj_dict:
                self.logger.error("You should add logical name for ports")
                raise Exception("You should add logical name for ports")

            for port_name, port in self.ports.items():
                # 'physical location in the form ip/module/port'
                port_name = port_name.lower().strip()
                if port_name in ports_obj_dict:
                    FullAddress = re.sub(r'PG.*?[^a-zA-Z0-9 ]', r'', ports_obj_dict[port_name].FullAddress)
                    physical_add = re.sub(r'[^./0-9 ]', r'', FullAddress)
                    self.logger.info("Logical Port %s will be reserved now on Physical location %s" %
                                     (str(port_name), str(physical_add)))
                    port.reserve(physical_add,force=True,wait_for_up=False)

        else:
            for port_name, port in self.ports.items():
                # 'physical location in the form ip/module/port'
                port.reserve(force=True)

        self.logger.info("Port Reservation Completed")

    def send_arp(self, context):
        """
        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """
        self.ixn.send_arp_ns()

    def start_devices(self, context):
        """
        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """
        self.ixn.protocols_start()

    def stop_devices(self, context):
        """
        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """

        self.ixn.protocols_stop()

    def start_traffic(self, context,blocking):
        """
        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """
        blocking = bool(blocking) if blocking in ["true", "True"] else False
        self.ixn.traffic_apply()
        self.ixn.l23_traffic_start()

    def stop_traffic(self, context):
        """
        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """

        self.ixn.l23_traffic_stop()


    def get_statistics(self, context, view_name,name_caption, output_type):
        output_file = output_type.lower().strip()
        if output_file != 'json' and output_file != 'csv':
            raise Exception("The output format should be json or csv")
        statistics = self.ixn.getStatistics(view_name)
        reservation_id = context.reservation.reservation_id
        my_api = self.get_api(context)
        if output_file.lower() == 'json':
            statistics = json.dumps(statistics, indent=4, sort_keys=True,ensure_ascii=False)
            # print statistics
            my_api.WriteMessageToReservationOutput(reservation_id, statistics)
        elif output_file.lower() == 'csv':
            output = io.BytesIO()
            w = csv.DictWriter(output, statistics.keys())
            w.writeheader()
            w.writerow(statistics)

            my_api.WriteMessageToReservationOutput(reservation_id,output.getvalue().strip('\r\n'))


