from dbus_next.service import ServiceInterface, method
import asyncio
from dbus_next.aio import MessageBus
from dbus_next import Message, MessageType
from ..shell.smtc import WindowsSMTC

class MediaControlService(ServiceInterface):
    def __init__(self, bus_instance: MessageBus):
        super().__init__('dev.farrel.FancyWSL')
        self.bus = bus_instance

        self.smtc_instance = WindowsSMTC()



        # self.bus.add_message_handler(self.playback_status_change_handler)

        # await self.percobaan(bus_instance)

    def playback_status_change_handler(self, message: Message):
        # if message.path == '/org/mpris/MediaPlayer2':
        print(message)
    
    async def percobaan(self):
        reply = await self.bus.call(Message(destination='org.freedesktop.DBus', path='/org/freedesktop/DBus',
                                            member='AddMatch', signature='s',
                                            body=['path=/org/mpris/MediaPlayer2']))
        
        # print(reply.message_type)
        # assert reply.message_type == MessageType.METHOD_RETURN
        self.bus.add_message_handler(self.playback_status_change_handler)
