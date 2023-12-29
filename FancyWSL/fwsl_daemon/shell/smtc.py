import logging
import winsdk.windows.media.playback as windows_media_playback
from winsdk.windows.media import (MediaPlaybackStatus, MediaPlaybackType, SystemMediaTransportControls,
                                  SystemMediaTransportControlsButtonPressedEventArgs,
                                  SystemMediaTransportControlsButton)
from winsdk.windows.storage.streams import RandomAccessStreamReference
import winsdk.windows.foundation as windows_foundation

logger = logging.getLogger(__name__)

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

    def __handle_button_press(self, _: SystemMediaTransportControls,
                              args: SystemMediaTransportControlsButtonPressedEventArgs):
        if (args.button == SystemMediaTransportControlsButton.PLAY or
            args.button == SystemMediaTransportControlsButton.PAUSE):
            self.__play_pause_callback(self.dbus_client_id)
        elif args.button == SystemMediaTransportControlsButton.PREVIOUS:
            self.__go_previous_callback(self.dbus_client_id)
        elif args.button == SystemMediaTransportControlsButton.NEXT:
            self.__go_next_callback(self.dbus_client_id)

    def update_state(self, playback_info: dict):
        if 'Metadata' in playback_info:
            metadata: dict = playback_info['Metadata'].value
            # FIXME: Maybe find a way to determine this from the MPRIS metadata (or does the MPRIS metadata
            # even contain this information?)
            self.__updater.type = MediaPlaybackType.MUSIC

            if 'xesam:artist' in metadata:
                # Apparently it's an array
                self.__updater.music_properties.artist = metadata['xesam:artist'].value[0]

                logger.info(f'WindowsSMTC "{self.dbus_client_id}" artist is '
                            f'now "{self.__updater.music_properties.artist}".')

            if 'xesam:albumArtist' in metadata:
                # Also an array
                self.__updater.music_properties.album_artist = metadata['xesam:albumArtist'].value[0]

                logger.info(f'WindowsSMTC "{self.dbus_client_id}" album artist is '
                            f'now "{self.__updater.music_properties.album_artist}".')

            if 'xesam:title' in metadata:
                self.__updater.music_properties.title = metadata['xesam:title'].value

                logger.info(f'WindowsSMTC "{self.dbus_client_id}" title is '
                            f'now "{self.__updater.music_properties.title}".')
                
            if 'mpris:artUrl' in metadata:
                def log_thumbnail_value(value: str):
                    logger.info(f'Thumbnail for player "{self.dbus_client_id}" is set to {value}.')

                art_url_value: str = metadata['mpris:artUrl'].value

                # Omit non-secure HTTP support, just in case.
                if art_url_value.startswith('https://'):
                    self.__updater.thumbnail = RandomAccessStreamReference.create_from_uri(
                        windows_foundation.Uri(art_url_value)
                    )

                    log_thumbnail_value(f'the URL "{art_url_value}"')

                elif art_url_value != '':
                    logger.warn(f'("{self.dbus_client_id}") The artUrl value "{art_url_value}" is '
                                '(currently) unsupported.')

            self.__updater.update()

        if 'PlaybackStatus' in playback_info:
            playback_status = playback_info['PlaybackStatus'].value

            logger.info(f'WindowsSMTC "{self.dbus_client_id}" playback status is set to {playback_status}.')

            if playback_status == 'Playing':
                self.__controls.playback_status = MediaPlaybackStatus.PLAYING
            elif playback_status == 'Paused':
                self.__controls.playback_status = MediaPlaybackStatus.PAUSED
            elif playback_status == 'Stopped':
                self.__controls.playback_status = MediaPlaybackStatus.STOPPED

        # Extra comparisons of the booleans here to ensure that the returned (pythonized) types are correct.
        if 'CanPlay' in playback_info:
            self.__controls.is_play_enabled = True if playback_info['CanPlay'].value == True else False
            logger.info(f'"{self.dbus_client_id}" CanPlay is {playback_info["CanPlay"].value}.')
        if 'CanPause' in playback_info:
            self.__controls.is_pause_enabled = True if playback_info['CanPause'].value == True else False
            logger.info(f'"{self.dbus_client_id}" CanPause is {playback_info["CanPause"].value}.')
        if 'CanGoNext' in playback_info:
            self.__controls.is_next_enabled = True if playback_info['CanGoNext'].value == True else False
            logger.info(f'"{self.dbus_client_id}" CanGoNext is {playback_info["CanGoNext"].value}.')
        if 'CanGoPrevious' in playback_info:
            self.__controls.is_previous_enabled = True if playback_info['CanGoPrevious'].value == True else False
            logger.info(f'"{self.dbus_client_id}" CanGoPrevious is {playback_info["CanGoPrevious"].value}.')


    def destroy(self):
        self.__controls.is_enabled = False
        logger.info(f'WindowsSMTC instance for client "{self.dbus_client_id}" is destroyed.')
        # TODO: There must be more to be done here.
