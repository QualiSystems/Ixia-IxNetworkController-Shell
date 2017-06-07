
import json
import csv
import io

from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext

from trafficgenerator.tgn_tcl import TgnTkMultithread
from ixnetwork.ixn_app import IxnApp
from ixnetwork.api.ixn_tcl import IxnTclWrapper
from ixnetwork.ixn_statistics_view import IxnStatisticsView, IxnFlowStatistics

import tg_helper


class IxnHandler(object):

    def __init__(self):
        self.logger = tg_helper.create_logger('c:/temp/ixnetwork_controller_logger.txt')

    def initialize(self, client_install_path, tcl_server, tcl_port):

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

    def load_config(self, context, ixia_config_file_name):

        self.ixn.load_config(ixia_config_file_name)
        config_ports = self.ixn.root.get_ports()

        for port in config_ports.values():
            port.release()

        reservation_id = context.reservation.reservation_id
        my_api = CloudShellSessionContext(context).get_api()

        reservation_ports = {}
        for port in tg_helper.get_reservation_ports(my_api, reservation_id):
            reservation_ports[my_api.GetAttributeValue(port.Name, 'Logical Name').Value.strip()] = port

        for name, port in config_ports.items():
            if name in reservation_ports:
                address = tg_helper.get_address(reservation_ports[name])
                self.logger.debug('Logical Port {} will be reserved on Physical location {}'.format(name, address))
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
        self.ixn.traffic_apply()
        self.ixn.l23_traffic_start(tg_helper.is_blocking(blocking))

    def stop_traffic(self):
        self.ixn.l23_traffic_stop()

    def get_statistics(self, context, view_name, output_type):

        if view_name == 'Flow Statistics':
            stats_obj = IxnFlowStatistics()
        else:
            stats_obj = IxnStatisticsView(view_name)

        stats_obj.read_stats()
        statistics = stats_obj.get_all_stats()
        if output_type.lower().strip() == 'json':
            statistics_str = json.dumps(statistics, indent=4, sort_keys=True, ensure_ascii=False)
            return json.loads(statistics_str)
        elif output_type.lower().strip() == 'csv':
            output = io.BytesIO()
            w = csv.DictWriter(output, stats_obj.captions)
            w.writeheader()
            for obj_name in statistics:
                w.writerow(statistics[obj_name])
            tg_helper.attach_stats_csv(context, self.logger, view_name, output.getvalue().strip())
            return output.getvalue().strip()
        else:
            raise Exception('Output type should be CSV/JSON - got "{}"'.format(output_type))

    def run_quick_test(self, context, test):

        self.ixn.quick_test_apply(test)
        return self.ixn.quick_test_start(test, blocking=True, timeout=3600 * 24)
