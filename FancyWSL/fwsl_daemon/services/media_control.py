import logging
from dbus_next.service import ServiceInterface, method
from dbus_next.aio import MessageBus
from dbus_next import Message, MessageType
from ..shell.smtc import WindowsSMTC

# Get logger for current module
logger = logging.getLogger(__name__)

class MediaControlService(ServiceInterface):
    def __init__(self, bus_instance: MessageBus):
        super().__init__('dev.farrel.FancyWSL')

        self.bus = bus_instance
        self.mpris_clients: dict[str, WindowsSMTC] = {}

        # FIXME: This overall logic assumes that FancyWSL has run before any potential media-playing apps
        # in WSL starts. This could be improved by e.g. reading the list of existing running media-playing
        # apps on FancyWSL startup (or at least at the time of instantiating this class).

    async def init_async(self):
        await self.__add_dbus_match('sender=org.freedesktop.DBus, path=/org/freedesktop/DBus, '
                                    'interface=org.freedesktop.DBus, member=NameOwnerChanged')
        
        await self.__add_dbus_match('path=/org/mpris/MediaPlayer2, '
                                    'interface=org.freedesktop.DBus.Properties, member=PropertiesChanged')
        # self.bus.add_message_handler(self.playback_status_change_handler)

        self.bus.add_message_handler(self.__signal_handler)

    async def __add_dbus_match(self, match_string: str) -> None:
        reply = await self.bus.call(Message(destination='org.freedesktop.DBus', path='/org/freedesktop/DBus',
                                            member='AddMatch', signature='s',
                                            body=[match_string]))
        
        assert reply.message_type == MessageType.METHOD_RETURN

    def __signal_handler(self, message: Message):
        if message.path == '/org/mpris/MediaPlayer2' and message.member == 'PropertiesChanged':
            self.__playback_status_change_handler(message.sender, message.body[1])
        elif (message.path == '/org/freedesktop/DBus' and message.member == 'NameOwnerChanged' and
              message.body[0].startswith('org.mpris.MediaPlayer2.')):
            # Let's use the unique names instead of the bus names here for simplicity of logic
            [_, old_owner, new_owner] = message.body
            if old_owner == '' and new_owner != '':
                self.__new_playback_instance(new_owner)
            elif old_owner != '' and new_owner == '':
                self.__destroy_playback_instance(old_owner)
    
    def __new_playback_instance(self, client_id: str):
        logger.info(f'add {client_id}')
        self.mpris_clients[client_id] = WindowsSMTC(client_id, self.__play_pause_request_handler)

    def __destroy_playback_instance(self, client_id: str):
        logger.info(f'remove {client_id}')
        self.mpris_clients[client_id].destroy()
        self.mpris_clients.pop(client_id)
    
    def __playback_status_change_handler(self, client_id: str, playback_info):
        self.mpris_clients[client_id].update_state(playback_info)

    async def __play_pause_request_handler(self, client_id: str):
        await self.bus.call(Message(destination=client_id, path='/org/mpris/MediaPlayer2',
                                    interface='org.mpris.MediaPlayer2.Player', member='PlayPause'))
