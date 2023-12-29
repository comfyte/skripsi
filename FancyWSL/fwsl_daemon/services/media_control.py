import logging
from functools import wraps
# import asyncio
# from asgiref.sync import async_to_sync
import subprocess
# from dbus_next.service import ServiceInterface, method
from dbus_next.aio import MessageBus
from dbus_next import Message, MessageType
from ..shell.smtc import WindowsSMTC

# Get logger for current module
logger = logging.getLogger(__name__)

def disregard_unregistered_client(original_function):
    @wraps(original_function)
    def wrapper_function(*args, **kwargs):
        try:
            return original_function(*args, **kwargs)
        except KeyError as e:
            logger.warning(f'Unknown client ("{e.args[0]}") disregarded.')
    return wrapper_function

class MediaControlService:
    def __init__(self, bus_instance: MessageBus, wsl_distro_name: str):
        self.bus = bus_instance
        self.wsl_distro_name = wsl_distro_name

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
    
    @disregard_unregistered_client
    def __new_playback_instance(self, client_id: str):
        logger.info(f'add {client_id}')
        self.mpris_clients[client_id] = WindowsSMTC(client_id,
                                                    self.wsl_distro_name,
                                                    play_pause_callback=self.__play_pause_request_handler,
                                                    go_previous_callback=self.__go_previous_request_handler,
                                                    go_next_callback=self.__go_next_request_handler)

    @disregard_unregistered_client
    def __destroy_playback_instance(self, client_id: str):
        logger.info(f'remove {client_id}')
        self.mpris_clients[client_id].destroy()
        self.mpris_clients.pop(client_id)
    
    @disregard_unregistered_client
    def __playback_status_change_handler(self, client_id: str, playback_info):
        self.mpris_clients[client_id].update_state(playback_info)

    def __play_pause_request_handler(self, client_id: str):
        # def future_done_callback(a):
        #     logger.info(f'Called PlayPause method to client "{client_id}".')
        #     logger.info(a)

        # FIXME: This only works because the underlying dbus-next library hasn't migrated this function to
        # a coroutine function yet; this would probably break when it eventually happens.
        # self.bus.send(Message(destination=client_id,
        #                       path='/org/mpris/MediaPlayer2',
        #                       interface='org.mpris.MediaPlayer2.Player',
        #                       member='PlayPause')).add_done_callback(future_done_callback)
        # async_to_sync(self.bus.call)(Message(destination=client_id,
        #                                      path='/org/mpris/MediaPlayer2',
        #                                      interface='org.mpris.MediaPlayer2.Player',
        #                                      member='PlayPause'))
        
        # logger.info(f'Called PlayPause method to client "{client_id}".')

        # HACK and FIXME
        _temporary_dbus_direct_method_call(wsl_distro_name=self.wsl_distro_name,
                                           destination=client_id,
                                           method_name='PlayPause')
        
    def __go_previous_request_handler(self):
        pass

    def __go_next_request_handler(self):
        pass

# HACK: This is currently calling `dbus-send` directly because I couldn't make the asynchronous stuff work
# yet. Please revert to the native Python handling soon after it's worked out!
def _temporary_dbus_direct_method_call(*, wsl_distro_name: str, destination: str, method_name: str):
    logger.warn(f'Using a temporary hack for calling D-Bus method "{method_name}" on '
                f'destination "{destination}".')
    
    dbus_send_command = ['dbus-send',
                         '--session',
                         '--type=method_call',
                         f'--dest={destination}',
                         '/org/mpris/MediaPlayer2',
                         f'org.mpris.MediaPlayer2.Player.{method_name}']
    subprocess.run(['wsl.exe', '-d', f'{wsl_distro_name}'] + dbus_send_command, check=True)
