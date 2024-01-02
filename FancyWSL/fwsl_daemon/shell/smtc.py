import logging
from typing import TypedDict
from pprint import pformat
import winsdk.windows.media.playback as windows_media_playback
from winsdk.windows.media import (MediaPlaybackStatus,
                                  MediaPlaybackType,
                                  SystemMediaTransportControls,
                                  SystemMediaTransportControlsButtonPressedEventArgs,
                                  SystemMediaTransportControlsButton)
from winsdk.windows.storage.streams import RandomAccessStreamReference
import winsdk.windows.foundation as windows_foundation

logger = logging.getLogger(__name__)

class MediaInfo(TypedDict):
    artist: str
    album_artist: str
    title: str
    album_art_url: str

class MediaAbilities(TypedDict):
    can_play: bool
    can_pause: bool
    can_go_previous: bool
    can_go_next: bool


class MediaState(TypedDict):
    media_type: MediaPlaybackType
    media_info: MediaInfo
    # playback_status: Literal['Playing', 'Paused', 'Stopped']
    playback_status: MediaPlaybackStatus
    abilities: MediaAbilities

class WindowsSMTC():
    def __init__(self,
                 current_client_id: str,
                 wsl_distro_name: str,
                 *,
                 play_pause_callback,
                 go_previous_callback,
                 go_next_callback) -> None:
        logger.info(f'Initialized WindowsSMTC for client "{current_client_id}".')

        self.dbus_client_id = current_client_id
        self.wsl_distro_name = wsl_distro_name

        # Assign the callbacks to this class instance
        self.__play_pause_callback = play_pause_callback
        self.__go_previous_callback = go_previous_callback
        self.__go_next_callback = go_next_callback

        self.__media_player = windows_media_playback.MediaPlayer()

        self.__controls = self.__media_player.system_media_transport_controls
        self.__media_player.command_manager.is_enabled = False

        self.__updater = self.__controls.display_updater

        self.__controls.is_enabled = True

        self.__controls.add_button_pressed(self.__handle_button_press)

    def __handle_button_press(self,
                              _: SystemMediaTransportControls,
                              args: SystemMediaTransportControlsButtonPressedEventArgs):
        if (args.button == SystemMediaTransportControlsButton.PLAY or
            args.button == SystemMediaTransportControlsButton.PAUSE):
            self.__play_pause_callback(self.dbus_client_id)
        elif args.button == SystemMediaTransportControlsButton.PREVIOUS:
            self.__go_previous_callback(self.dbus_client_id)
        elif args.button == SystemMediaTransportControlsButton.NEXT:
            self.__go_next_callback(self.dbus_client_id)

    def update_state(self, current_playback_state: MediaState):
        logger.info('Received below details for updating SMTC state for MPRIS client '
                    f'"{self.dbus_client_id}".\n' + pformat(current_playback_state))

        if 'media_type' in current_playback_state:
            self.__updater.type = current_playback_state['media_type']
        
        if 'media_info' in current_playback_state:
            current_media_info = current_playback_state['media_info']

            if 'artist' in current_media_info:
                self.__updater.music_properties.artist = current_media_info['artist']

            if 'album_artist' in current_media_info:
                self.__updater.music_properties.album_artist = current_media_info['album_artist']

            if 'title' in current_media_info:
                self.__updater.music_properties.title = current_media_info['title']

            if 'album_art_url' in current_media_info:
                # Omit non-secure HTTP support, just in case.
                if current_media_info['album_art_url'].startswith('https://'):
                    self.__updater.thumbnail = RandomAccessStreamReference.create_from_uri(
                        windows_foundation.Uri(current_media_info['album_art_url'])
                    )

                elif current_media_info['album_art_url'] != '':
                    logger.warn(f'("{self.dbus_client_id}") The album art URL value "{current_media_info["album_art_url"]}" is '
                                '(currently) unsupported.')

            self.__updater.update()

        if 'playback_status' in current_playback_state:
            self.__controls.playback_status = current_playback_state['playback_status']

        if 'abilities' in current_playback_state:
            abilities = current_playback_state['abilities']
            if 'can_play' in abilities:
                self.__controls.is_play_enabled = abilities['can_play']
            if 'can_pause' in abilities:
                self.__controls.is_pause_enabled = abilities['can_pause']
            if 'can_go_previous' in abilities:
                self.__controls.is_previous_enabled = abilities['can_go_previous']
            if 'can_go_next' in abilities:
                self.__controls.is_next_enabled = abilities['can_go_next']

        logger.info(f'SMTC state for MPRIS client "{self.dbus_client_id}" has successfully been updated.')
        
    def destroy(self):
        self.__controls.is_enabled = False
        logger.info(f'WindowsSMTC instance for client "{self.dbus_client_id}" is destroyed.')
        # TODO: There must be more to be done here.
