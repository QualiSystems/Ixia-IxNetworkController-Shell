
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface

from ixn_handler import IxnHandler
import tg_helper


class IxNetworkControllerDriver(ResourceDriverInterface):

    def __init__(self):
        self.handler = IxnHandler()

    def initialize(self, context):
        """
        :type context:  cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """

        self.handler.initialize(context.resource.attributes['Client Install Path'],
                                context.resource.attributes['Controller Address'],
                                context.resource.attributes['Controller TCP Port'])

    def load_config(self, context, ixn_config_file_name):
        """ Load IxNetwork configuration file and reserve ports.

        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        :param ixn_config_file_name: full path to IxNetwork configuration file (ixncfg).
        """

        tg_helper.enqueue_keep_alive(context)
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

    def cleanup(self):
        self.handler.tearDown()

    def keep_alive(self, context, cancellation_context):

        while not cancellation_context.is_cancelled:
            pass
        if cancellation_context.is_cancelled:
            self.handler.tearDown()
