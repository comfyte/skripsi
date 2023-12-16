import winsdk
from dbus_next.aio import MessageBus
from dbus_next.service import ServiceInterface, signal
from dbus_next.auth import AuthAnnonymous
import asyncio
# from . import services

from services.notifications import NotificationHandlerService

async def main():
    bus = await MessageBus('tcp:host=localhost,port=17395,family=ipv4', auth=AuthAnnonymous()).connect()

    # bus.export('/dev/farrel/FancyWSL', NotificationHandlerService())
    notificationHandlerInterface = NotificationHandlerService()
    bus.export('/org/freedesktop/Notifications', notificationHandlerInterface)
    # await bus.request_name('dev.farrel.FancyWSL')
    await bus.request_name('org.freedesktop.Notifications')

    await asyncio.sleep(2)

    # notificationHandlerInterface.Changed()

    await bus.wait_for_disconnect()



if __name__ == '__main__':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        asyncio.get_event_loop().run_until_complete(main())
    except KeyboardInterrupt:
        print('Exiting...')
