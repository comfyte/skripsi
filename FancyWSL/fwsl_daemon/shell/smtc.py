import winsdk.windows.media.playback as windows_media_playback
from winsdk.windows.media import (MediaPlaybackStatus, MediaPlaybackType, SystemMediaTransportControls,
                                  SystemMediaTransportControlsButtonPressedEventArgs,
                                  SystemMediaTransportControlsButton)

class WindowsSMTC():
    def __init__(self, current_client_id: str, play_pause_callback) -> None:
        self.dbus_client_id = current_client_id
        self.__play_pause_callback = play_pause_callback

        self.__media_player = windows_media_playback.MediaPlayer()

        self.__controls = self.__media_player.system_media_transport_controls
        self.__media_player.command_manager.is_enabled = False

        self.__updater = self.__controls.display_updater

        self.__controls.is_enabled = True

        self.__controls.add_button_pressed(self.__handle_button_press)

        # self.updater.update()

    def __handle_button_press(self, sender: SystemMediaTransportControls,
                              args: SystemMediaTransportControlsButtonPressedEventArgs):
        if (args.button == SystemMediaTransportControlsButton.PLAY or
            args.button == SystemMediaTransportControlsButton.PAUSE):
            self.__play_pause_callback(self.dbus_client_id)

    def update_state(self, playback_info: dict):
        if 'Metadata' in playback_info:
            print(playback_info)
            metadata: dict = playback_info['Metadata'].value
            # FIXME: Maybe find a way to determine this from the MPRIS metadata (or does the MPRIS metadata
            # even contain this information?)
            self.__updater.type = MediaPlaybackType.MUSIC

            # print('metadata is below')
            # print(metadata)

            # print('the metadata value property is below')
            # print(metadata.value)

            if 'xesam:artist' in metadata:
                print(type(metadata['xesam:artist']))
                print(type(metadata['xesam:artist'].value))

                # Apparently it's an array
                self.__updater.music_properties.artist = metadata['xesam:artist'].value[0]
            if 'xesam:albumArtist' in metadata:
                # Also an array
                self.__updater.music_properties.album_artist = metadata['xesam:albumArtist'].value[0]
            if 'xesam:title' in metadata:
                self.__updater.music_properties.title = metadata['xesam:title'].value

            self.__updater.update()

        if 'PlaybackStatus' in playback_info:
            playback_status = playback_info['PlaybackStatus'].value

            if playback_status == 'Playing':
                self.__controls.playback_status = MediaPlaybackStatus.PLAYING
            elif playback_status == 'Paused':
                self.__controls.playback_status = MediaPlaybackStatus.PAUSED
            elif playback_status == 'Stopped':
                self.__controls.playback_status = MediaPlaybackStatus.STOPPED

        # Extra comparisons of the booleans here to ensure that the returned (pythonized) types are correct.
        if 'CanPlay' in playback_info:
            self.__controls.is_play_enabled = True if playback_info['CanPlay'].value == True else False
        if 'CanPause' in playback_info:
            self.__controls.is_pause_enabled = True if playback_info['CanPause'].value == True else False
        if 'CanGoNext' in playback_info:
            self.__controls.is_next_enabled = True if playback_info['CanGoNext'].value == True else False
        if 'CanGoPrevious' in playback_info:
            self.__controls.is_previous_enabled = True if playback_info['CanGoPrevious'].value == True else False

    def destroy(self):
        self.__controls.is_enabled = False
        # TODO: There must be more to be done here.
