import logging
# from logging import _Level, LogRecord
# import sys
from argparse import ArgumentParser
import asyncio

# from dbus_next.aio import MessageBus
# from dbus_next.auth import AuthAnnonymous

from .helpers.platform_verifications import preliminary_platform_checks
from .helpers.spawn_win32_alert_window import spawn_win32_alert_window
# from .helpers.wsl_manager import wsl_get_distro_list
# from .helpers.obtain_bus_address import obtain_bus_address
from .shell.persistent_tray_icon import PersistentTrayIcon
from .fwsld import FancyWSLDaemon
# from .services.notifications import NotificationHandlerService
# from .services.mpris import MediaControlService
# from .shell.toast_notification import clear_all_fwsl_notifications

# _persistent_tray_icon: PersistentTrayIcon = None

# _connections = set()

# Define clean-up function before exiting the program.
# def cleanup_before_exiting():
#     _logger.info('Beginning clean-up...')

#     _logger.info('Clean-up complete.')


# async def fwsl_daemon():
#     # Do checks first
#     try:
#         preliminary_platform_checks()
#     except RuntimeError as e:
#         _logger.error(e.args[0])
#         spawn_win32_alert_window('An error occurred', e.args[0])
#         sys.exit(1)

#     _logger.info('Starting FancyWSL Daemon...')

#     _distro_list = wsl_get_distro_list()
#     distro_list = [item['name'] for item in _distro_list if item['version'] == 2]

#     try:
#         default_distro_name = [item for item in _distro_list if item['is_default']][0]['name']
#     except IndexError:
#         raise RuntimeError('The WSL default distribution seem to have version 1 (WSL 1). Please specify the '
#                            'distribution in the argument when launching FancyWSL or alternatively change '
#                            'the WSL default distribution version to 2 (WSL 2).')

#     global distro_name

#     # Use the default distro if the distro argument is not provided.
#     if distro_name is None:
#         _logger.info('No specific WSL distribution is supplied in the execution argument. '
#                      f'Using the default WSL distribution ({default_distro_name}).')
#         distro_name = default_distro_name
    
#     global _persistent_tray_icon
#     _persistent_tray_icon = PersistentTrayIcon((distro_list, distro_list.index(default_distro_name),
#                                                 distro_list.index(distro_name)),
#                                                 exit_callback=lambda _: cleanup_before_exiting())
    
#     # Obtain the bus address for the specified distro.
#     try:
#         bus_address = obtain_bus_address(distro_name)
#     except RuntimeError as e:
#         spawn_win32_alert_window(f'Error connecting to "{distro_name}" distribution', e.args[0])
#         # print('a')
#         # sys.exit(1)
#         return

#     _logger.info(f'Connecting to distribution "{distro_name}" with bus address "{bus_address}"...')

#     try:
#         global bus
#         bus = await MessageBus(bus_address, auth=AuthAnnonymous()).connect()
#         _logger.info('Connected to bus successfully.')
#     except:
#         _logger.error('Some error happened. Exiting FancyWSL Daemon...')
#         # sys.exit(1)
#         return

#     await attach_services_to_bus()

#     await bus.wait_for_disconnect()
#     _logger.info('Connection to '
#                  f'distribution "{distro_name}" with '
#                  f'bus address "{bus_address}" '
#                  'is disconnected.')

def setup_and_get_arguments():
    parser = ArgumentParser('FancyWSL Daemon')

    # root_group = parser.add_mutually_exclusive_group

    # primary_subparser = root_parser.add_subparsers

    # parser.add_argument('-l', '--list-wsl-distributions')

    # parser.add_argument('-d', '--wsl-distribution',
    #                     help='Specify the WSL distribution to be used by FancyWSL.', type=str)
    parser.add_argument('-v', '--verbose', help='Print more logs verbosely.', action='store_true')
    
    return parser.parse_args()

class _AlertWindowLogHandler(logging.Handler):
    def __init__(self, level = logging.ERROR) -> None:
        super().__init__(level)

    def emit(self, record) -> None:
        # name, msg = record

        partial_title = ['An error occured']
        if record.name != 'root':
            partial_title.append(f'in {record.name}')

        # This call is actually blocking because it waits for the user response for the
        # displayed alert window.
        spawn_win32_alert_window(' '.join(partial_title), record.getMessage())
    
def main():
    args = setup_and_get_arguments()

    # if args.list_wsl_distributions

    logging.basicConfig(format='FWSL LOG | %(asctime)s | (%(name)s) %(levelname)s: %(message)s',
                        level=logging.INFO if args.verbose else logging.WARNING)
    root_logger = logging.getLogger()

    # Add additional handler for displaying logs of level "ERROR" as GUI alert window.
    root_logger.addHandler(_AlertWindowLogHandler())

    try:
        preliminary_platform_checks()
    except RuntimeError as e:
        root_logger.error(e.args[0])
        # spawn_win32_alert_window('An error occured while launching FancyWSL daemon', e.args[0])
        # return
        raise

    # distro_name_arg = args.wsl_distribution
    # if distro_name_arg is not None:
    #     global distro_name
    #     distro_name = distro_name_arg

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Run main loop
    # asyncio.get_event_loop().run_until_complete(fwsl_daemon())
    # fwsld_singleton_instance = FancyWSLDaemon()
    fwsld_instance = FancyWSLDaemon()
    asyncio.run(fwsld_instance.start())

    # The main loop will end when the bus has disconnected
    # _persistent_tray_icon.manual_shutdown()
    # _logger.info('Exiting FancyWSL Daemon...')

if __name__ == '__main__':
    main()
