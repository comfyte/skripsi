import sys
import asyncio
from dbus_next.aio import MessageBus
from dbus_next.auth import AuthAnnonymous
from .shell.persistent_tray_icon import PersistentTrayIcon
from .services.notifications import NotificationHandlerService

async def attach_interfaces_to_bus(bus: MessageBus):
    # org.freedesktop.Notifications
    bus.export('/org/freedesktop/Notifications', NotificationHandlerService())
    await bus.request_name('org.freedesktop.Notifications')

async def main():
    print('Starting FancyWSL Daemon...')

    try:
        # TODO: The bus address is currently still hard-coded
        bus = await MessageBus('tcp:host=localhost,port=17395,family=ipv4',
                               auth=AuthAnnonymous()).connect()
        print('Connected to bus successfully')
    except:
        print('Some error happened. Exiting FancyWSL Daemon...')
        sys.exit(1)

    await attach_interfaces_to_bus(bus)

    # Define clean-up function before exiting the program
    def cleanup_before_exiting():
        bus.disconnect()

    def persistent_tray_icon_quit_handler(_):
        cleanup_before_exiting()
        print('Killed the system tray icon')

    PersistentTrayIcon(persistent_tray_icon_quit_handler)

    await bus.wait_for_disconnect()
    print('Disconnected from bus')

if __name__ == '__main__':
    # Workaround because we're running on Windows (instead of Unix-like/Linux)
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.get_event_loop().run_until_complete(main())

    # The main loop will end when the bus has disconnected
    print('Exiting FancyWSL Daemon...')
