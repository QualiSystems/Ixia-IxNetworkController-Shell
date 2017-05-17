
import json
import csv
import io
import logging
import time

from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext
from trafficgenerator.tgn_tcl import TgnTkMultithread
from ixnetwork.ixn_app import IxnApp
from ixnetwork.api.ixn_tcl import IxnTclWrapper
from ixnetwork.ixn_statistics_view import IxnStatisticsView, IxnFlowStatistics
from helper.quali_rest_api_helper import create_quali_api_instance


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

    def initialize(self, client_install_path, tcl_server, tcl_port):

        log_file = 'c:/temp/ixnetwork_controller_logger.txt'
        self.logger = logging.getLogger('root')
        self.logger.addHandler(logging.FileHandler(log_file))
        self.logger.setLevel(logging.DEBUG)

        self.tcl_interp = TgnTkMultithread()
        self.tcl_interp.start()
        self.logger.debug('client_install_path = ' + client_install_path)
        api_wrapper = IxnTclWrapper(self.logger, client_install_path, self.tcl_interp)
        self.ixn = IxnApp(self.logger, api_wrapper)

        if tcl_server.lower() in ('na', ''):
            tcl_server = 'localhost'
        if not tcl_port:
            tcl_port = 8009
        self.logger.debug("connecting to tcl server {} at {} port".format(tcl_server, tcl_port))
        self.ixn.connect(tcl_server=tcl_server, tcl_port=tcl_port)

    def tearDown(self):
        self.tcl_interp.stop()

    def get_api(self, context):
        return CloudShellSessionContext(context).get_api()

    def load_config(self, context, ixia_config_file_name):

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

    def send_arp(self):
        self.ixn.send_arp_ns()

    def start_protocols(self):
        self.ixn.protocols_start()

    def stop_protocos(self):
        self.ixn.protocols_stop()

    def start_traffic(self, blocking):
        blocking = bool(blocking) if blocking in ["true", "True"] else False
        self.ixn.traffic_apply()
        self.ixn.l23_traffic_start(blocking)

    def stop_traffic(self):
        self.ixn.l23_traffic_stop()

    def get_statistics(self, context, view_name, output_type):
        output_file = output_type.lower().strip()

        if view_name == 'Flow Statistics':
            stats_obj = IxnFlowStatistics()
        else:
            stats_obj = IxnStatisticsView(view_name)

        stats_obj.read_stats()
        statistics = stats_obj.get_all_stats()
        reservation_id = context.reservation.reservation_id
        my_api = self.get_api(context)
        if output_file.lower() == 'json':
            statistics_str = json.dumps(statistics, indent=4, sort_keys=True, ensure_ascii=False)
            return json.loads(statistics_str)
        elif output_file.lower() == 'csv':
            output = io.BytesIO()
            w = csv.DictWriter(output, stats_obj.captions)
            w.writeheader()
            for obj_name in statistics:
                w.writerow(statistics[obj_name])
            quali_api_helper = create_quali_api_instance(context, self.logger)
            quali_api_helper.login()
            full_file_name = view_name.replace(' ', '_') + '_' + time.ctime().replace(' ', '_') + '.csv'
            quali_api_helper.upload_file(context.reservation.reservation_id,
                                         file_name=full_file_name,
                                         file_stream=output.getvalue().strip())
            my_api.WriteMessageToReservationOutput(reservation_id,
                                                   'Statistics view saved in attached file - ' + full_file_name)
            return output.getvalue().strip('\r\n')
        else:
            raise Exception('Output type should be CSV/JSON')

    def run_quick_test(self, context, test):

        self.ixn.quick_test_apply(test)
        result = self.ixn.quick_test_start(test, blocking=True)
        my_api = self.get_api(context)
        reservation_id = context.reservation.reservation_id
        my_api.WriteMessageToReservationOutput(reservation_id, 'result = ' + result)
