import logging
import sys
from argparse import ArgumentParser
import asyncio
from dbus_next.aio import MessageBus
from dbus_next.auth import AuthAnnonymous
from winsdk.windows.ui.notifications import ToastNotificationManager
from .helpers.verify_platform import verify_platform
from .shell.persistent_tray_icon import PersistentTrayIcon
from .services.notifications import NotificationHandlerService
from .services.mpris import MediaControlService
from .helpers.constants import NOTIFICATION_GROUP_NAME

async def attach_services_to_bus(bus: MessageBus, *, wsl_distro_name):
    # org.freedesktop.Notifications
    bus.export('/org/freedesktop/Notifications', NotificationHandlerService(wsl_distro_name))
    await bus.request_name('org.freedesktop.Notifications')

    media_control_service = MediaControlService(bus, wsl_distro_name)
    await media_control_service.init_async()

# Define clean-up function before exiting the program.
def cleanup_before_exiting(*, bus_instance: MessageBus, logger: logging.Logger):
    logger.info('Beginning clean-up...')

    ToastNotificationManager.history.remove_group(NOTIFICATION_GROUP_NAME)
    logger.info(f'Cleared all Windows ToastNotification with group name "{NOTIFICATION_GROUP_NAME}".')

    bus_instance.disconnect()

    logger.info('Clean-up complete.')

# Program entry point
async def fwsl_daemon(bus_address: str, logger: logging.Logger):
    # Wrap everything in a try-except so that we have a global exception handler (assuming that the rest of
    # the code outside this main function will always work flawlessly).
    try:
        # Do checks first
        try:
            platform_info = verify_platform()
        except RuntimeError as e:
            logger.error(e.args[0])
            sys.exit(1)

        logger.info('Starting FancyWSL Daemon...')

        if not bus_address.startswith('tcp:'):
            logger.error('The supplied bus address is not a TCP address. Currently, only TCP addresses are '
                         'supported by FancyWSL. Exiting...')
            sys.exit(1)

        logger.info(f'Connecting to bus address "{bus_address}"...')

        try:
            bus = await MessageBus(bus_address, auth=AuthAnnonymous()).connect()
            logger.info('Connected to bus successfully.')
        except:
            logger.error('Some error happened. Exiting FancyWSL Daemon...')
            sys.exit(1)

        await attach_services_to_bus(bus, wsl_distro_name=platform_info['wsl_distro_name'])


        def persistent_tray_icon_quit_handler(_):
            logger.info('Received quit request.')
            cleanup_before_exiting(bus_instance=bus, logger=logger)
            logger.info('Killed the system tray icon.')

        PersistentTrayIcon(bus_address, persistent_tray_icon_quit_handler)

        await bus.wait_for_disconnect()
        logger.info(f'Connection to bus "{bus_address}" disconnected.')
    except Exception as e:
        logger.error(f'An error happened to FancyWSL (details are below).')
        logger.error(e)

        # TODO: Attempt to show a visible error message to the user (probably by reusing
        # the toast notification thing).
    finally:
        # TODO: Find out what the "Unbound" type found within this block (or the `except` block) means.
        cleanup_before_exiting(bus_instance=bus, logger=logger)

if __name__ == '__main__':
    argument_parser = ArgumentParser('FancyWSL Daemon')

    argument_parser.add_argument('--bus-address',
                                 help=('Specify the bus address (currently only TCP addresses are '
                                       'supported) to be used by FancyWSL.'),
                                 type=str,
                                 required=True)
    argument_parser.add_argument('--verbose', help='Print more logs verbosely.', action='store_true')
    
    args = argument_parser.parse_args()

    # Set up logging.
    log_level = logging.WARNING if args.verbose is None else logging.INFO
    logging.basicConfig(format='FWSL LOG | %(asctime)s | (%(name)s) %(levelname)s: %(message)s',
                        level=log_level)
    logger = logging.getLogger(__name__)


    # Workaround because we're running on Windows (instead of Unix-like/Linux).
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Run main loop
    asyncio.get_event_loop().run_until_complete(fwsl_daemon(args.bus_address, logger))

    # The main loop will end when the bus has disconnected
    logger.info('Exiting FancyWSL Daemon...')
