import logging
from typing import Callable
from infi.systray import SysTrayIcon

_logger = logging.getLogger('tray_icon')

class PersistentTrayIcon:
    """
    Make sure to call `set_distro_connection_count(value)` after instantiating, otherwise the system tray
    hover text will display "Not connected yet".
    """
    def __init__(self, *, exit_callback: Callable) -> None:
        # TODO: Check first if the exit_callback function is properly given and properly exists

        self.instance = SysTrayIcon(None,
                                    self.__generate_hover_text_with_info('Not connected yet'),
                                    None,
                                    exit_callback)

        # Non-blocking
        self.instance.start()

        _logger.info('Summoned the system tray icon')

    def __generate_hover_text_with_info(self, info_text: str):
        return f'FancyWSL Daemon ({info_text})'

    def set_distro_connection_count(self, value: int):
        if self.instance:
            text = self.__generate_hover_text_with_info(f'Connected to {value} distributions')
            self.instance.update(hover_text=text)
