import logging
from typing import Callable

from ..helpers.spawn_win32_alert_window import spawn_win32_alert_window

from infi.systray import SysTrayIcon

# Get logger for current module
_logger = logging.getLogger(__name__)

class PersistentTrayIcon:
    def __init__(self, distro_data: tuple[list[str], int, int],
                 *,
                 exit_callback: Callable) -> None:
        """
        Note: `distro_data` argument is a tuple with the first element being a list of distributions, the
        second element being the index of the default distribution, and the third element being the index of
        the currently-used distribution (in regard to the first list).
        """
        # distro_list, default_distro_index, current_distro_index = distro_data
        distro_list, default_distro_index, active_distro_index = distro_data

        # TODO: Check first if the exit_callback function is properly given and properly exists

        dn: Callable[[str, int], str] = lambda n, i: n if i != default_distro_index else f'{n} (Default)'

        # menu_items = ((f'Switch WSL distribution',
        #               None,
        #               tuple([tuple([dn(distro_name, distro_index) + (' (reload)' if distro_index == active_distro_index else ''), None, lambda _: _temporary_alert_because_distro_switching_is_not_implemented_yet(distro_name)]) for distro_index, distro_name in enumerate(distro_list) if distro_index != active_distro_index])),)

        _active_distro_name = dn(distro_list[active_distro_index], active_distro_index)

        self._is_already_shut_down_automatically = False

        def wrap_exit_callback(systray):
            self._is_already_shut_down_automatically = True
            exit_callback(systray)

        self.instance = SysTrayIcon(None, f'FancyWSL Daemon (Connected to {_active_distro_name})', None, wrap_exit_callback)
        self.instance.start()
        _logger.info('Summoned the system tray icon')

    def manual_shutdown(self):
        if self._is_already_shut_down_automatically:
            _logger.warn('The system tray instance has been shut down automatically; ignoring '
                         'manual shutdown method call...')
            return
        
        return self.instance.shutdown()

# FIXME (and TODO)
# def _temporary_alert_because_distro_switching_is_not_implemented_yet(target_distro_name: str):
#     _logger.warning(f'User wants to switch to distribution "{target_distro_name}", but seamless '
#                     'distribution-switching is not implemented yet.')
    
#     return spawn_win32_alert_window('Distribution-switching capability is not implemented yet',
#                                     f'To switch to {target_distro_name}, please manually exit the current '
#                                     f'FancyWSL daemon and relaunch with argument "-d {target_distro_name}" '
#                                     'at the command-line because seamless distribution switching is not '
#                                     'implemented (yet) at the moment.')
