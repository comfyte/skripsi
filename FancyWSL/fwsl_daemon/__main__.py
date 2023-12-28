import logging
import sys
from argparse import ArgumentParser
import asyncio
from dbus_next.aio import MessageBus
from dbus_next.auth import AuthAnnonymous
from .helpers.verify_platform import verify_platform
from .shell.persistent_tray_icon import PersistentTrayIcon
from .services.notifications import NotificationHandlerService
from .services.media_control import MediaControlService

# Set logging to display all messages (to make debugging easier).
logging.basicConfig(format='FWSL LOG | %(asctime)s | (%(name)s) %(levelname)s: %(message)s', level=logging.INFO)

# Get logger for current module
logger = logging.getLogger(__name__)

async def attach_services_to_bus(bus: MessageBus):
    # org.freedesktop.Notifications
    bus.export('/org/freedesktop/Notifications', NotificationHandlerService())
    await bus.request_name('org.freedesktop.Notifications')

    media_control_service = MediaControlService(bus)
    await media_control_service.init_async()

async def fwsl_daemon(bus_address: str):
    # Do checks first
    try:
        verify_platform()
    except RuntimeError:
        sys.exit(1)

    logger.info('Starting FancyWSL Daemon...')

    if not bus_address.startswith('tcp:'):
        logger.error('The supplied bus address is not a TCP address. Currently, only TCP addresses are supported '
                     'by FancyWSL. Exiting...')
        sys.exit(1)

    logger.info(f'Connecting to bus address "{bus_address}"...')

    try:
        bus = await MessageBus(bus_address, auth=AuthAnnonymous()).connect()
        logger.info('Connected to bus successfully.')
    except:
        logger.error('Some error happened. Exiting FancyWSL Daemon...')
        sys.exit(1)

    await attach_services_to_bus(bus)

    # Define clean-up function before exiting the program
    def cleanup_before_exiting():
        bus.disconnect()

    def persistent_tray_icon_quit_handler(_):
        cleanup_before_exiting()
        logger.info('Killed the system tray icon.')

    PersistentTrayIcon(bus_address, persistent_tray_icon_quit_handler)

    await bus.wait_for_disconnect()
    logger.info(f'Connection to bus "{bus_address}" disconnected.')

if __name__ == '__main__':
    argument_parser = ArgumentParser('FancyWSL Daemon')
    argument_parser.add_argument('--bus-address', help='Specify the bus address (currently only TCP address '
                                 'is supported) to be used by FancyWSL.', type=str, required=True)
    args = argument_parser.parse_args()

    # Workaround because we're running on Windows (instead of Unix-like/Linux)
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Run main loop
    asyncio.get_event_loop().run_until_complete(fwsl_daemon(args.bus_address))

    # The main loop will end when the bus has disconnected
    logger.info('Exiting FancyWSL Daemon...')
