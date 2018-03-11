
from cloudshell.traffic.driver import TrafficControllerDriver
import cloudshell.traffic.tg_helper as tg_helper

from ixn_handler import IxnHandler


class IxNetworkControllerDriver(TrafficControllerDriver):

    def __init__(self):
        super(self.__class__, self).__init__()
        self.handler = IxnHandler()

    def load_config(self, context, ixn_config_file_name):
        """ Load IxNetwork configuration file and reserve ports.

        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        :param ixn_config_file_name: full path to IxNetwork configuration file (ixncfg).
        """

        self.logger.info('ixn_config_file_name = ' + ixn_config_file_name)
        super(self.__class__, self).load_config(context)
        self.handler.load_config(context, ixn_config_file_name)
        return ixn_config_file_name + ' loaded, ports reserved'

    def send_arp(self, context):
        """ Send ARP for all objects.

        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """

        self.handler.send_arp()

    def start_protocols(self, context):
        """ Start all protocols.

        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """

        self.handler.start_protocols()

    def stop_protocols(self, context):
        """ Stop all protocols.

        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """

        self.handler.stop_protocols()

    def start_traffic(self, context, blocking):
        """ Start all L2/3 traffic items.

        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        :param blocking: True - wait until traffic stops, False - start traffic and return immediately.
        """

        self.handler.start_traffic(blocking)

    def stop_traffic(self, context):
        """ Stop all L2/3 traffic items.

        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """

        self.handler.stop_traffic()

    def get_statistics(self, context, view_name, output_type):
        """ Get statistics for specific view.

        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        :param view_name: requested statistics view name.
        :param output_type: JSON/CSV.
        """

        return self.handler.get_statistics(context, view_name, output_type)

    def run_quick_test(self, context, test):
        """ Run quick test.

        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        :param test: name of quick test to run.
        """

        quick_test_resut = self.handler.run_quick_test(context, test)
        tg_helper.write_to_reservation_out(context, 'Quick test result = ' + quick_test_resut)
        return quick_test_resut

    #
    # Parent commands are not visible so we re define them in child.
    #

    def initialize(self, context):
        super(self.__class__, self).initialize(context)

    def cleanup(self):
        super(self.__class__, self).cleanup()

    def keep_alive(self, context, cancellation_context):
        super(self.__class__, self).keep_alive(context, cancellation_context)
