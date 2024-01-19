import logging
import sys
from argparse import ArgumentParser
import asyncio

from dbus_next.aio import MessageBus
from dbus_next.auth import AuthAnnonymous
from winsdk.windows.ui.notifications import ToastNotificationManager

from .helpers.platform_verifications import preliminary_checks
from .helpers.spawn_win32_alert_window import spawn_win32_alert_window
from .helpers.wsl_manager import wsl_get_distro_list
from .helpers.obtain_bus_address import obtain_bus_address
from .shell.persistent_tray_icon import PersistentTrayIcon
from .services.notifications import NotificationHandlerService
from .services.mpris import MediaControlService
from .helpers.constants import NOTIFICATION_GROUP_NAME

_logger: logging.Logger = None

bus: MessageBus = None
distro_name: str = None

_persistent_tray_icon: PersistentTrayIcon = None

_is_already_attached = False
async def attach_services_to_bus():
    global _is_already_attached

    if _is_already_attached:
        raise RuntimeError('Services are already attached to the bus.')
    
    # Notification handling
    bus.export('/org/freedesktop/Notifications', NotificationHandlerService(distro_name))
    await bus.request_name('org.freedesktop.Notifications')

    # Media control
    media_control_service = MediaControlService(bus, distro_name)
    await media_control_service.init_async()

    _is_already_attached = True

# Define clean-up function before exiting the program.
def cleanup_before_exiting():
    _logger.info('Beginning clean-up...')

    ToastNotificationManager.history.remove_group(NOTIFICATION_GROUP_NAME)
    _logger.info(f'Cleared all Windows ToastNotification with group name "{NOTIFICATION_GROUP_NAME}".')

    if bus is not None:
        bus.disconnect()

    _logger.info('Clean-up complete.')

async def fwsl_daemon():
    # Do checks first
    try:
        preliminary_checks()
    except RuntimeError as e:
        _logger.error(e.args[0])
        spawn_win32_alert_window('An error occurred', e.args[0])
        sys.exit(1)

    _logger.info('Starting FancyWSL Daemon...')

    _distro_list = wsl_get_distro_list()
    distro_list = [item['name'] for item in _distro_list if item['version'] == 2]

    try:
        default_distro_name = [item for item in _distro_list if item['is_default']][0]['name']
    except IndexError:
        raise RuntimeError('The WSL default distribution seem to have version 1 (WSL 1). Please specify the '
                           'distribution in the argument when launching FancyWSL or alternatively change '
                           'the WSL default distribution version to 2 (WSL 2).')

    global distro_name

    # Use the default distro if the distro argument is not provided.
    if distro_name is None:
        _logger.info('No specific WSL distribution is supplied in the execution argument. '
                     f'Using the default WSL distribution ({default_distro_name}).')
        distro_name = default_distro_name
    
    global _persistent_tray_icon
    _persistent_tray_icon = PersistentTrayIcon((distro_list, distro_list.index(default_distro_name),
                                                distro_list.index(distro_name)),
                                                exit_callback=lambda _: cleanup_before_exiting())
    
    # Obtain the bus address for the specified distro.
    try:
        bus_address = obtain_bus_address(distro_name)
    except RuntimeError as e:
        spawn_win32_alert_window(f'Error connecting to "{distro_name}" distribution', e.args[0])
        # print('a')
        # sys.exit(1)
        return

    _logger.info(f'Connecting to distribution "{distro_name}" with bus address "{bus_address}"...')

    try:
        global bus
        bus = await MessageBus(bus_address, auth=AuthAnnonymous()).connect()
        _logger.info('Connected to bus successfully.')
    except:
        _logger.error('Some error happened. Exiting FancyWSL Daemon...')
        # sys.exit(1)
        return

    await attach_services_to_bus()

    await bus.wait_for_disconnect()
    _logger.info('Connection to '
                 f'distribution "{distro_name}" with '
                 f'bus address "{bus_address}" '
                 'is disconnected.')

def setup_and_get_arguments():
    argument_parser = ArgumentParser('FancyWSL Daemon')

    argument_parser.add_argument('-d', '--wsl-distribution',
                                 help='Specify the WSL distribution to be used by FancyWSL.', type=str)
    argument_parser.add_argument('-v', '--verbose', help='Print more logs verbosely.', action='store_true')
    
    return argument_parser.parse_args()

def setup_global_logger(is_verbose: bool) -> None:
    global _logger

    if _logger is not None:
        # return
        raise RuntimeError('Logger is already set up!')

    logging.basicConfig(format='FWSL LOG | %(asctime)s | (%(name)s) %(levelname)s: %(message)s',
                        level=logging.INFO if is_verbose else logging.WARNING)
    
    _logger = logging.getLogger(__name__)

def main():
    args = setup_and_get_arguments()

    setup_global_logger(args.verbose)

    distro_name_arg = args.wsl_distribution
    if distro_name_arg is not None:
        global distro_name
        distro_name = distro_name_arg

    # Workaround because we're running on Windows (instead of Unix-like/Linux).
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Run main loop
    asyncio.get_event_loop().run_until_complete(fwsl_daemon())

    # The main loop will end when the bus has disconnected
    _persistent_tray_icon.manual_shutdown()
    _logger.info('Exiting FancyWSL Daemon...')

if __name__ == '__main__':
    main()
