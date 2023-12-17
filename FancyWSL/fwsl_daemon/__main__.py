import sys
from argparse import ArgumentParser
import asyncio
from dbus_next.aio import MessageBus
from dbus_next.auth import AuthAnnonymous
from .helpers.verify_platform import verify_platform
from .shell.persistent_tray_icon import PersistentTrayIcon
from .services.notifications import NotificationHandlerService

async def attach_interfaces_to_bus(bus: MessageBus):
    # org.freedesktop.Notifications
    bus.export('/org/freedesktop/Notifications', NotificationHandlerService())
    await bus.request_name('org.freedesktop.Notifications')

async def fwsl_daemon(bus_address: str):
    # Do checks first
    try:
        verify_platform()
    except RuntimeError:
        sys.exit(1)

    print('Starting FancyWSL Daemon...')

    if not bus_address.startswith('tcp:'):
        print('The supplied bus address is not a TCP address. Currently, only TCP addresses are supported '
              'by FancyWSL. Exiting...', file=sys.stderr)
        sys.exit(1)

    print(f'Connecting to bus address "{bus_address}"...')

    try:
        bus = await MessageBus(bus_address, auth=AuthAnnonymous()).connect()
        print('Connected to bus successfully.')
    except:
        print('Some error happened. Exiting FancyWSL Daemon...', file=sys.stderr)
        sys.exit(1)

    await attach_interfaces_to_bus(bus)

    # Define clean-up function before exiting the program
    def cleanup_before_exiting():
        bus.disconnect()

    def persistent_tray_icon_quit_handler(_):
        cleanup_before_exiting()
        print('Killed the system tray icon.')

    PersistentTrayIcon(persistent_tray_icon_quit_handler)

    await bus.wait_for_disconnect()
    print(f'Connection to bus "{bus_address}" disconnected.')

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
    print('Exiting FancyWSL Daemon...')
