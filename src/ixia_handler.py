
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


def get_reservation_ports(session, reservation_id):
    """ Get all Generic Traffic Generator Port in reservation.

    :return: list of all Generic Traffic Generator Port resource objects in reservation
    """
    reservation_ports = []
    reservation = session.GetReservationDetails(reservation_id).ReservationDescription
    for resource in reservation.Resources:
        if resource.ResourceModelName == 'Generic Traffic Generator Port':
            reservation_ports.append(resource)
    return reservation_ports


class IxiaHandler(object):

    def initialize(self, context):
        """
        :type context: cloudshell.shell.core.driver_context.InitCommandContext
        """

        log_file = 'ixnetwork_controller_logger.txt'
        self.logger = logging.getLogger('root')
        self.logger.addHandler(logging.FileHandler(log_file))
        self.logger.setLevel(logging.DEBUG)

        self.tcl_interp = TgnTkMultithread()
        self.tcl_interp.start()
        client_install_path = context.resource.attributes['Client Install Path']
        self.logger.debug('client_install_path = ' + client_install_path)
        api_wrapper = IxnTclWrapper(self.logger, client_install_path, self.tcl_interp)
        self.ixn = IxnApp(self.logger, api_wrapper)

        tcl_server = context.resource.address
        if tcl_server.lower() in ('na', ''):
            tcl_server = 'localhost'
        tcl_port = context.resource.attributes['Controller TCP Port']
        if not tcl_port:
            tcl_port = 8009
        self.logger.debug("connecting to tcl server {} at {} port".format(tcl_server, tcl_port))
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
        self.config_ports = self.ixn.root.get_ports()

        reservation_id = context.reservation.reservation_id
        my_api = self.get_api(context)

        reservation_ports = {}
        for port in get_reservation_ports(my_api, reservation_id):
            reservation_ports[my_api.GetAttributeValue(port.Name, 'Logical Name').Value.strip()] = port

        for name, port in self.config_ports.items():
            if name in reservation_ports:
                address = reservation_ports[name].FullAddress
                self.logger.debug('Logical Port {} will be reserved Physical location {}'.format(name, address))
                port.reserve(address, force=True, wait_for_up=False)
            else:
                self.logger.error('Configuration port "{}" not found in reservation ports {}'.
                                  format(port, reservation_ports.keys()))
                raise Exception('Configuration port "{}" not found in reservation ports {}'.
                                format(port, reservation_ports.keys()))

        self.logger.info("Port Reservation Completed")

    def send_arp(self, context):
        """
        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """
        self.ixn.send_arp_ns()

    def start_protocols(self, context):
        """
        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """
        self.ixn.protocols_start()

    def stop_protocos(self, context):
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
            return statistics
        elif output_file.lower() == 'csv':
            output = io.BytesIO()
            w = csv.DictWriter(output, statistics.keys())
            w.writeheader()
            w.writerow(statistics)
            my_api.WriteMessageToReservationOutput(reservation_id, output.getvalue().strip('\r\n'))
            return output.getvalue().strip('\r\n')
        else:
            raise Exception('Output type should be CSV/JSON')

    def run_quick_test(self, context, test):
        """
        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """
        self.ixn.quick_test_apply(test)
        result = self.ixn.quick_test_start(test, blocking=True)
        my_api = self.get_api(context)
        reservation_id = context.reservation.reservation_id
        my_api.WriteMessageToReservationOutput(reservation_id, 'result = ' + result)
