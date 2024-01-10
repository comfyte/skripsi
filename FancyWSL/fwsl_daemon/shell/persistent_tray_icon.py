import logging
from pystray import Icon, Menu, MenuItem
from PIL import Image as PILImage, ImageDraw as PILImageDraw
from typing import Callable
from ..helpers.types import DistroItem

# Get logger for current module
_logger = logging.getLogger(__name__)

# Width and height
ICON_DIMENSION = 64

def _generate_icon():
    image = PILImage.new('RGB', (ICON_DIMENSION, ICON_DIMENSION), 'black')
    image_draw = PILImageDraw.Draw(image)

    midpoint = ICON_DIMENSION / 2
    bounding_circle_radius = (7/8) / ICON_DIMENSION

    image_draw.regular_polygon((midpoint, midpoint, bounding_circle_radius), 4, 45, 'white', None)

    return image

class PersistentTrayIcon():
    def __init__(self,
                 distro_list_getter: Callable[[], list[DistroItem] | None],
                #  bus_address_getter: Callable[[], str | None],
                 distro_change_callback: Callable[[str], None],
                 exit_callback: Callable) -> None:
        # self.__menu = 
        # super().__init__('fwsl-daemon', _generate_icon(), 'FancyWSL Daemon')
        # get_bus_address = lambda _: MenuItem(f'Listening to "{bus_address_getter()}" if ')

        # self.__exit_callback = exit_callback

        def get_connection_info_text():
            # distro_name = distro_name_getter()
            # bus_address = bus_address_getter()
            # distro_name = list(filter(lambda item: item['is_chosen'] == True, distro_list_getter()))[0]
            # print(distro_list_getter())
            # distro_name = [item for item in distro_list_getter() if item['is_chosen']][0]

            # is_available = distro_name is not None and bus_address is not None
            # is_available = bus_address is not None

            # FIXME: Avoid doing this because this will call the same getter function two times (the
            # other one is within the `get_distro_option()` function).
            distro_list = distro_list_getter()

            print(distro_list)

            # TODO: Optimize the code to avoid such kind of repetition.
            not_connected_menu_item = MenuItem('Not connected yet', None, enabled=False)

            if not distro_list:
                return not_connected_menu_item
            
            try:
                distro_name = [item for item in distro_list if item['is_chosen']][0]
            except IndexError:
                return not_connected_menu_item

            return MenuItem(f'Connected to "{distro_name}".', None, enabled=False)

            # return MenuItem(f'Connected to "{distro_name}".' if is_available
            #                 else 'Not connected yet', None, enabled=False)
        
        def get_distro_switcher_option():
            distro_list = distro_list_getter()
            is_ready = bool(distro_list)

            distro_menu_items = ([MenuItem(item['name'] + (' (Default)' if item['is_default'] else ''),
                                           lambda _: distro_change_callback(item['name']))
                                        #    radio=True,
                                        #    checked=item['is_chosen'])
                                  for item in distro_list]
                                 if is_ready
                                 else
                                 [MenuItem('Distributions are not ready yet.', None, enabled=False)])
            
            return MenuItem('Switch WSL distribution', Menu(*distro_menu_items), enabled=is_ready)
        
        def handle_exit():
            self.t__icon_instance.stop()
            exit_callback()
        
        menu = Menu(MenuItem('FancyWSL Daemon', None, enabled=False),
                    get_connection_info_text(),
                    Menu.SEPARATOR,
                    get_distro_switcher_option(),
                    Menu.SEPARATOR,
                    MenuItem('Exit', handle_exit))

        self.t__icon_instance = Icon('fwsl-daemon', _generate_icon(), 'FancyWSL Daemon', menu)
        self.t__icon_instance.run_detached()
        _logger.info('Summoned the system tray icon')

    def notify(self, title: str, message: str):
        self.t__icon_instance.notify(message, title)

    # def __update_menu(self):
    #     self.__menu

    # def update_distribution_info(self):
    
    # # Always pass every data/info on every update for good measure.
    # def update_state(self,
    #                  listen_address: str | None,
    #                  distro_list: list[DistributionItem] | None,
    #                  exit_callback: Callable):
        # # TODO: Better handle scenarios e.g. where the WSL distro list is changed (a distro is
        # # added or uninstalled) during the runtime of FancyWSL.

        # listen_text = (f'Listening to "{listen_address}"' if listen_address is not None
        #                else 'Not connected yet')
        
        # if distro_list is not None:
        #     distro_option = MenuItem('Switch WSL distribution...', )

        # is_distro_selection_ready = distro_list is not None
        # distro_items = (Menu(MenuItem(name + (' (Default)' if is_default else ''), radio=True,
        #                               checked=is_chosen) for name, is_default, is_chosen in distro_list)
        #                      if is_distro_selection_ready else None)
        # distro_option = MenuItem('Switch WSL distribution...', distro_items,
        #                          enabled=is_distro_selection_ready)

        # menu = Menu(MenuItem('FancyWSL Daemon', enabled=False),
        #             MenuItem(listen_text, enabled=False),
        #             Menu.SEPARATOR,
        #             distro_option,
        #             Menu.SEPARATOR,
        #             MenuItem('Exit', lambda _: self.__handle_exit(exit_callback)))
        
        # # self.__icon_instance.update_menu()

# a = pystray.Icon('a', )
