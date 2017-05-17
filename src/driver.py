
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.context_utils import get_resource_name

from ixn_handler import IxiaHandler


class IxNetworkControllerDriver(ResourceDriverInterface):

    def __init__(self):
        self.handler = IxiaHandler()

    def initialize(self, context):
        """
        :type context:  cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """

        self.handler.initialize(context.resource.attributes['Client Install Path'],
                                context.resource.attributes['Controller Address'],
                                context.resource.attributes['Controller TCP Port'])

    def load_config(self, context, ixia_config_file_name):
        """ Load IxNetwork configuration file and reserve ports.

        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        :param ixia_config_file_name: full path to IxNetwork configuration file (ixncfg).
        """

        my_api = self.handler.get_api(context)
        reservation_id = context.reservation.reservation_id
        resource_name = get_resource_name(context=context)
        my_api.EnqueueCommand(reservationId=reservation_id, targetName=resource_name, commandName="keep_alive",
                              targetType="Service")

        self.handler.load_config(context, ixia_config_file_name)

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

        self.handler.run_quick_test(context, test)

    def cleanup(self):
        self.handler.tearDown()
        pass

    def keep_alive(self, context, cancellation_context):

        while not cancellation_context.is_cancelled:
            pass
        if cancellation_context.is_cancelled:
            self.handler.tearDown()
