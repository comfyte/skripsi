import winsdk.windows.media.playback as windows_media_playback
from winsdk.windows.media import MediaPlaybackStatus

class WindowsSMTC():
    def __init__(self) -> None:
        self.media_player = windows_media_playback.MediaPlayer()
        self.controls = self.media_player.system_media_transport_controls
        # self.media_player.command_manager.is_enabled = False

        self.updater = self.controls.display_updater

        self.controls.is_enabled = True
        self.controls.is_play_enabled = True
        self.controls.is_pause_enabled = True
        self.controls.is_next_enabled = True
        self.controls.is_previous_enabled = True

        self.controls.playback_status = MediaPlaybackStatus.PLAYING

        self.updater.update()

    def destroy():
        pass