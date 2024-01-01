import logging
from functools import wraps
import subprocess
from dbus_next.aio import MessageBus
from dbus_next import Message, MessageType
from ..shell.smtc import WindowsSMTC, MediaState, MediaPlaybackType, MediaPlaybackStatus

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

        self.bus.add_message_handler(self.__signal_handler)

    async def __add_dbus_match(self, match_string: str) -> None:
        reply = await self.bus.call(Message(destination='org.freedesktop.DBus', path='/org/freedesktop/DBus',
                                            member='AddMatch', signature='s',
                                            body=[match_string]))
        
        assert reply.message_type == MessageType.METHOD_RETURN

    def __signal_handler(self, message: Message):
        if message.path == '/org/mpris/MediaPlayer2' and message.member == 'PropertiesChanged':
            self.__playback_status_change_handler(message.sender, message.body[1])
        elif (message.path == '/org/freedesktop/DBus' and
              message.member == 'NameOwnerChanged' and
              message.body[0].startswith('org.mpris.MediaPlayer2.')):
            # Let's use the unique names instead of the bus names here for simplicity of logic
            [well_known_name, old_owner, new_owner] = message.body
            if old_owner == '' and new_owner != '':
                unique_name = new_owner
                logger.info(f'Detected a new MPRIS client with unique name "{unique_name}" and '
                            f'known name "{well_known_name}".')
                self.__new_playback_instance(unique_name)
            elif old_owner != '' and new_owner == '':
                unique_name = old_owner
                logger.info(f'Client "{unique_name}" ("{well_known_name}") is not on bus anymore.')
                self.__destroy_playback_instance(unique_name)

            client_count = len(self.mpris_clients)
            is_plural = client_count == 1
            logger.info(f'There {"is" if is_plural else "are"} now {client_count} MPRIS '
                        f'client{"s" if is_plural else ""} handled by FancyWSL '
                        f'({", ".join(self.mpris_clients.keys())}).')
    
    @disregard_unregistered_client
    def __new_playback_instance(self, client_id: str):
        self.mpris_clients[client_id] = WindowsSMTC(client_id,
                                                    self.wsl_distro_name,
                                                    play_pause_callback=self.__play_pause_request_handler,
                                                    go_previous_callback=self.__go_previous_request_handler,
                                                    go_next_callback=self.__go_next_request_handler)

    @disregard_unregistered_client
    def __destroy_playback_instance(self, client_id: str):
        self.mpris_clients[client_id].destroy()
        self.mpris_clients.pop(client_id)
    
    @disregard_unregistered_client
    def __playback_status_change_handler(self, client_id: str, playback_info):
        current_playback_state: MediaState = {}

        # FIXME: Maybe find a way to determine this from the MPRIS metadata (or does the MPRIS metadata
        # even contain this information?)
        current_playback_state['media_type'] = MediaPlaybackType.MUSIC

        if 'Metadata' in playback_info:
            metadata: dict = playback_info['Metadata'].value

            if 'xesam:artist' in metadata:
                current_playback_state['media_info']['artist'] = metadata['xesam:artist'].value[0]
            if 'xesam:albumArtist' in metadata:
                current_playback_state['media_info']['album_artist'] = metadata['xesam:albumArtist'].value[0]
            if 'xesam:title' in metadata:
                current_playback_state['media_info']['title'] = metadata['xesam:title'].value
            if 'mpris:artUrl' in metadata:
                current_playback_state['media_info']['album_art_url'] = metadata['mpris:artUrl'].value

        if 'PlaybackStatus' in playback_info:
            matches = {
                'Playing': MediaPlaybackStatus.PLAYING,
                'Paused': MediaPlaybackStatus.PAUSED,
                'Stopped': MediaPlaybackStatus.STOPPED
            }
            current_playback_state['playback_status'] = matches[playback_info['PlaybackStatus'].value]

        # Extra comparisons of the booleans here to ensure that the returned (pythonized) types are correct.
        if 'CanPlay' in playback_info:
            current_playback_state['abilities']['can_play'] = True if playback_info['CanPlay'].value == True else False
        if 'CanPause' in playback_info:
            current_playback_state['abilities']['can_pause'] = True if playback_info['CanPause'].value == True else False
        if 'CanGoPrevious' in playback_info:
            current_playback_state['abilities']['can_go_previous'] = True if playback_info['CanGoPrevious'].value == True else False
        if 'CanGoNext' in playback_info:
            current_playback_state['abilities']['can_go_next'] = True if playback_info['CanGoNext'].value == True else False

        self.mpris_clients[client_id].update_state(current_playback_state)

    def __play_pause_request_handler(self, client_id: str):
        # HACK and FIXME
        _temporary_dbus_direct_method_call(wsl_distro_name=self.wsl_distro_name,
                                           destination=client_id,
                                           method_name='PlayPause')
        
    def __go_previous_request_handler(self, client_id: str):
        # HACK and FIXME
        _temporary_dbus_direct_method_call(wsl_distro_name=self.wsl_distro_name,
                                           destination=client_id,
                                           method_name='Previous')

    def __go_next_request_handler(self, client_id: str):
        # HACK and FIXME
        _temporary_dbus_direct_method_call(wsl_distro_name=self.wsl_distro_name,
                                           destination=client_id,
                                           method_name='Next')

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
