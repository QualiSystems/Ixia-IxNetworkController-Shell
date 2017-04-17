
import re
import json
import csv
import io
import logging

from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext
from cloudshell.shell.core.driver_context import AutoLoadDetails
from trafficgenerator.tgn_tcl import TgnTkMultithread
from ixnetwork.ixn_app import IxnApp
from ixnetwork.api.ixn_tcl import IxnTclWrapper
from ixnetwork.ixn_statistics_view import IxnStatisticsView, IxnFlowStatistics


class IxiaHandler(object):

    def initialize(self, context):
        """
        :type context: cloudshell.shell.core.driver_context.InitCommandContext
        """

        log_file = 'ixnetwork_controller_logger.txt'
        client_install_path = context.resource.attributes['Client Install Path']
        logging.basicConfig(filename=log_file, level=logging.DEBUG)
        self.logger = logging.getLogger('root')
        self.logger.addHandler(logging.FileHandler(log_file))
        self.logger.setLevel('DEBUG')

        self.tcl_interp = TgnTkMultithread()
        self.tcl_interp.start()
        api_wrapper = IxnTclWrapper(self.logger, client_install_path, self.tcl_interp)

        self.ixn = IxnApp(self.logger, api_wrapper)

        tcl_server = context.resource.address
        if tcl_server.lower() in ('na', ''):
            tcl_server = 'localhost'
        tcl_port = context.resource.attributes['Controller TCP Port']
        if not tcl_port:
            tcl_port = 8009
        self.logger.info("connecting to tcl server at {} port".format(tcl_server, tcl_port))
        self.ixn.connect(tcl_server=tcl_server, tcl_port=tcl_port)

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

    def load_config(self, context, ixia_config_file_name):
        """
        :param str stc_config_file_name: full path to STC configuration file (tcc or xml)
        :param context: the context the command runs on
        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """

        self.ixn.load_config(ixia_config_file_name)
        self.ports = self.ixn.root.get_ports()

        reservation_id = context.reservation.reservation_id
        my_api = self.get_api(context)
        response = my_api.GetReservationDetails(reservationId=reservation_id)

        search_chassis = "Ixia Chassis"
        search_port = "Port"
        chassis_objs_dict = dict()
        ports_obj = []

        for resource in response.ReservationDescription.Resources:
            if resource.ResourceModelName == search_chassis:
                chassis_objs_dict[resource.FullAddress] = {'chassis': resource, 'ports': list()}
        for resource in response.ReservationDescription.Resources:
            if resource.ResourceFamilyName == search_port:
                chassis_adr = resource.FullAddress.split('/')[0]
                if chassis_adr in chassis_objs_dict:
                    chassis_objs_dict[chassis_adr]['ports'].append(resource)
                    ports_obj.append(resource)

        ports_obj_dict = dict()
        for port in ports_obj:
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
                port.reserve(physical_add, force=True, wait_for_up=False)

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

    def start_traffic(self, context, blocking):
        """
        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """
        blocking = bool(blocking) if blocking in ["true", "True"] else False
        self.ixn.traffic_apply()
        self.ixn.l23_traffic_start(blocking)

    def stop_traffic(self):
        """
        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """

        self.ixn.l23_traffic_stop()

    def get_statistics(self, context, view_name, output_type):
        output_file = output_type.lower().strip()
        if output_file != 'json' and output_file != 'csv':
            raise Exception("The output format should be json or csv")

        if view_name == 'Flow Statistics':
            stats_obj = IxnFlowStatistics()
        else:
            stats_obj = IxnStatisticsView(view_name)
        stats_obj.read_stats()
        statistics = stats_obj.statistics
        reservation_id = context.reservation.reservation_id
        my_api = self.get_api(context)
        if output_file.lower() == 'json':
            statistics = json.dumps(statistics, indent=4, sort_keys=True, ensure_ascii=False)
            # print statistics
            my_api.WriteMessageToReservationOutput(reservation_id, statistics)
        elif output_file.lower() == 'csv':
            output = io.BytesIO()
            w = csv.DictWriter(output, statistics.keys())
            w.writeheader()
            w.writerow(statistics)

            my_api.WriteMessageToReservationOutput(reservation_id, output.getvalue().strip('\r\n'))
