import logging
from functools import wraps
import subprocess
from typing import Literal
from dbus_next.aio import MessageBus
from dbus_next import Message, MessageType
from ..shell.smtc import WindowsSMTC, MediaState, MediaPlaybackType, MediaPlaybackStatus

_logger = logging.getLogger('mpris')

def disregard_unregistered_client(original_function):
    @wraps(original_function)
    def wrapper_function(*args, **kwargs):
        try:
            return original_function(*args, **kwargs)
        except KeyError as e:
            key_name: str = e.args[0]
            if key_name.startswith(':'):
                # It means that the current key_name is a client unique name.
                _logger.warning(f'Unknown client ("{key_name}") disregarded.')
            else:
                raise e
    return wrapper_function

class MediaControlService:
    """
    You must call the `attach()` method first before being able to use this class instance.
    """
    def __init__(self, bus_instance: MessageBus, distro_name: str):
        self.bus = bus_instance
        self.distro_name = distro_name

        self.mpris_clients: dict[str, WindowsSMTC] = {}

        # FIXME: This overall logic assumes that FancyWSL has run before any potential media-playing apps
        # in WSL starts. This could be improved by e.g. reading the list of existing running media-playing
        # apps on FancyWSL startup (or at least at the time of instantiating this class).

    async def attach(self):
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
                _logger.info(f'Detected a new MPRIS client with unique name "{unique_name}" and '
                            f'known name "{well_known_name}".')
                self.__new_playback_instance(unique_name)
            elif old_owner != '' and new_owner == '':
                unique_name = old_owner
                _logger.info(f'Client "{unique_name}" ("{well_known_name}") is not on bus anymore.')
                self.__destroy_playback_instance(unique_name)

            client_count = len(self.mpris_clients)
            is_plural = client_count != 1
            _logger.info(f'There {"are" if is_plural else "is"} now {client_count} MPRIS '
                        f'client{"s" if is_plural else ""} handled by FancyWSL '
                        f'({", ".join(self.mpris_clients.keys())}).')
    
    @disregard_unregistered_client
    def __new_playback_instance(self, client_id: str):
        smtc_instance = WindowsSMTC(client_id,
                                    self.distro_name,
                                    play_pause_callback=self.__play_pause_request_handler,
                                    go_previous_callback=self.__go_previous_request_handler,
                                    go_next_callback=self.__go_next_request_handler)
        
        # Some clients like chromium don't broadcast some necessary properties right away, so we need to
        # proactively get the property values.
        smtc_instance.update_state({
            'abilities': {
                'can_play': _temporary_get_mpris_player_property(distro_name=self.distro_name,
                                                                 destination=client_id,
                                                                 property_name='CanPlay'),
                'can_pause': _temporary_get_mpris_player_property(distro_name=self.distro_name,
                                                                  destination=client_id,
                                                                  property_name='CanPause')
            }
        })

        self.mpris_clients[client_id] = smtc_instance

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

            # Initialize the parent dict first.
            current_playback_state['media_info'] = {}

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

        if any(key_name in playback_info for key_name in ['CanPlay',
                                                          'CanPause',
                                                          'CanGoPrevious',
                                                          'CanGoNext']):
            # Initialize the parent dict first.
            current_playback_state['abilities'] = {}

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
        _temporary_call_mpris_method(distro_name=self.distro_name,
                                           destination=client_id,
                                           method_name='PlayPause')
        
    def __go_previous_request_handler(self, client_id: str):
        # HACK and FIXME
        _temporary_call_mpris_method(distro_name=self.distro_name,
                                           destination=client_id,
                                           method_name='Previous')

    def __go_next_request_handler(self, client_id: str):
        # HACK and FIXME
        _temporary_call_mpris_method(distro_name=self.distro_name,
                                           destination=client_id,
                                           method_name='Next')

# HACK: These functions below are currently calling `dbus-send` directly because I couldn't make the
# asynchronous stuff work yet. Please revert to the native Python handling soon after it's worked out!

def _temporary_call_mpris_method(*, distro_name: str, destination: str, method_name: str) -> None:
    _logger.warn(f'Using a temporary hack for calling D-Bus method "{method_name}" on '
                f'destination "{destination}".')
    
    dbus_send_command = ['dbus-send',
                         '--session',
                         '--type=method_call',
                         f'--dest={destination}',
                         '/org/mpris/MediaPlayer2',
                         f'org.mpris.MediaPlayer2.Player.{method_name}']
    subprocess.run(['wsl.exe', '-d', distro_name] + dbus_send_command, check=True)

def _temporary_get_mpris_player_property(*,
                                         distro_name: str,
                                         destination: str,
                                         property_name: Literal['CanPlay',
                                                                'CanPause',
                                                                'CanGoPrevious',
                                                                'CanGoNext']) -> bool:
    _logger.warn(f'Using a temporary hack for getting the "{property_name}" property '
                f'of MPRIS client "{destination}".')
    
    dbus_send_command = ['dbus-send',
                         '--session',
                         '--type=method_call',
                         '--print-reply',
                         f'--dest={destination}',
                         '/org/mpris/MediaPlayer2',
                         'org.freedesktop.DBus.Properties.Get',
                         'string:org.mpris.MediaPlayer2.Player',
                         f'string:{property_name}']
    
    result = subprocess.run(['wsl.exe', '-d', distro_name] + dbus_send_command,
                            check=True,
                            capture_output=True,
                            encoding='utf-8')
    
    # HACK and FIXME: This parsing logic is likely very hacky.
    parsed_result = result.stdout.split()
    print(parsed_result)
    value_string = parsed_result[parsed_result.index('boolean') + 1]
    if value_string == 'true':
        return True
    elif value_string == 'false':
        return False
    else:
        raise ValueError(f'An error occured in getting the "{property_name}" property '
                         f'of the MPRIS client "{destination}".')
