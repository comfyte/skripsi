import logging
from typing import Callable
import pprint

from infi.systray import SysTrayIcon

# Get logger for current module
logger = logging.getLogger(__name__)

class PersistentTrayIcon:
    def __init__(self, distro_data: tuple[list[str], int, int],
                 *,
                 switch_distro_callback: Callable[[str], None],
                 exit_callback: Callable[[str], None]) -> None:
        """
        Note: `distro_data` argument is a tuple with the first element being a list of distributions, the
        second element being the index of the default distribution, and the third element being the index of
        the currently-used distribution (in regard to the first list).
        """
        # distro_list, default_distro_index, current_distro_index = distro_data
        distro_list, default_distro_index, active_distro_index = distro_data

        # TODO: Check first if the exit_callback function is properly given and properly exists

        # suffix_for_default_distro = lambda b:

        # dn: Callable[[str, bool], str] = lambda n, b: n if not b else f'{n} (Default)'
        dn: Callable[[str, int], str] = lambda n, i: n if i != default_distro_index else f'{n} (Default)'

        # menu_items = ('Switch WSL distribution '
        #               f'(currently connected to {dn(distro_list[active_distro_index], active_distro_index)})',
        #               None,
        #               ((dn(distro_name, distro_index) + (' (reload)' if distro_index == active_distro_index else ''),
        #                 lambda: switch_distro_callback(distro_index, self.instance.shutdown))
        #                for distro_name, distro_index in enumerate(distro_list)))

        menu_items = ((f'Switch WSL distribution (currently connected to {dn(distro_list[active_distro_index], active_distro_index)})',
                      None,
                      tuple([tuple([dn(distro_name, distro_index) + (' (reload)' if distro_index == active_distro_index else ''), None, lambda: switch_distro_callback(distro_index, self.instance.shutdown)]) for distro_index, distro_name in enumerate(distro_list)])),)

        
        pprint.PrettyPrinter().pprint(menu_items)

        self.instance = SysTrayIcon(None, 'FancyWSL Daemon', menu_items, exit_callback)
        self.instance.start()
        logger.info('Summoned the system tray icon')
