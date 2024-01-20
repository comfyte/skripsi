import logging
from typing import Callable

from infi.systray import SysTrayIcon

# from ..helpers.spawn_win32_alert_window import spawn_win32_alert_window

_logger = logging.getLogger('tray_icon')

class PersistentTrayIcon:
    """
    Make sure to call `set_distro_connection_count(value)` after instantiating, otherwise the system tray
    hover text will display "Not connected yet".
    """
    def __init__(self, *, exit_callback: Callable) -> None:
        # self.__product_name = 'FancyWSL Daemon'

        # TODO: Check first if the exit_callback function is properly given and properly exists

        self.instance = SysTrayIcon(None,
                                    self.__generate_hover_text_with_info('Not connected yet'),
                                    None,
                                    exit_callback)

        # Non-blocking
        self.instance.start()

        # self.distro_connection_count = distro_connection_count

        _logger.info('Summoned the system tray icon')

    def __generate_hover_text_with_info(self, info_text: str):
        return f'FancyWSL Daemon ({info_text})'

    # @property
    # def distro_connection_count(self) -> int:
    #     return self.__distro_connection_count
    
    # @distro_connection_count.setter
    # def distro_connection_count(self, value: int):
    def set_distro_connection_count(self, value: int):
        # self.__distro_connection_count = value
        if self.instance:
            # self.instance.update(hover_text=' '.join(self.__product_name,
            #                                          '(Connected '
            #                                          f'to {self.__distro_connection_count} distributions)'))
            # self.instance.update(hover_text=f'{self.__product_name} (Connected '
            #                      f'to {self.distro_connection_count} distributions)')
            # self.instance.update(hover_text=self.__generate_hover_text_with_info(' '.join(['Connected',
            #                                                                                'to',
            #                                                                                self.distro_connection_count])))
            # hover_text = self.__generate_hover_text_with_info('Connected '
            #                                                   f'to {self.distro_connection_count} distributions')
            # text = self.__generate_hover_text_with_info(' '.join(['Connected',
            #                                                             'to',
            #                                                             self.distro_connection_count,
            #                                                             'distributions']))
            text = self.__generate_hover_text_with_info(f'Connected to {value} distributions')
            self.instance.update(hover_text=text)

# FIXME (and TODO)
# def _temporary_alert_because_distro_switching_is_not_implemented_yet(target_distro_name: str):
#     _logger.warning(f'User wants to switch to distribution "{target_distro_name}", but seamless '
#                     'distribution-switching is not implemented yet.')
    
#     return spawn_win32_alert_window('Distribution-switching capability is not implemented yet',
#                                     f'To switch to {target_distro_name}, please manually exit the current '
#                                     f'FancyWSL daemon and relaunch with argument "-d {target_distro_name}" '
#                                     'at the command-line because seamless distribution switching is not '
#                                     'implemented (yet) at the moment.')
