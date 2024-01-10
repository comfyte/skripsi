import logging
import sys
from argparse import ArgumentParser
import asyncio
from dbus_next.aio import MessageBus
from dbus_next.auth import AuthAnnonymous
from typing import Callable, TypedDict
from winsdk.windows.ui.notifications import ToastNotificationManager
from .helpers.platform_verifications import preliminary_checks, verify_wsl_distro_readiness
from .helpers.obtain_bus_address import obtain_bus_address
from .helpers.wsl_manager import wsl_get_distro_list
from .shell.persistent_tray_icon import PersistentTrayIcon
from .services.notifications import NotificationHandlerService
from .services.mpris import MediaControlService
from .helpers.types import DistroItem
from .helpers.constants import NOTIFICATION_GROUP_NAME

# File-scoped global logger.
_logger: logging.Logger

# global_disconnect: Callable[[], None]

# class CurrentConnectionInfo(TypedDict):
# class CommonState(TypedDict):
# class CurrentState(TypedDict):
#     distro_list: list[DistroItem]
    # current_bus_address: str
    # current_distro_name: str

distro_list: list[DistroItem] | None = None

def refresh_distro_list() -> None:
    query_result = wsl_get_distro_list()

    # distro_list = [{'name': item['name'],
    #                 'is_default': item['is_default'],
    #                 'is_chosen': } for item in query_result]

    global distro_list
    distro_list = []

    for distro_item in query_result:
        if distro_item['version'] != 2:
            continue

        name = distro_item['name']
        is_default = distro_item['is_default']
        is_chosen = fwsl_bus_connection.distro_name == name if fwsl_bus_connection is not None else False

        distro_list.append({'name': name,
                            'is_default': is_default,
                            'is_chosen': is_chosen})

class _FWSLBusConnection:
    def __init__(self, distro_name: str):
        verify_wsl_distro_readiness(distro_name)

        self.bus_address = obtain_bus_address(distro_name)
        self.distro_name = distro_name

        self.__is_ready: bool = False

        # self.is_takeover_in_progress: bool = False
        self.was_manually_disconnected: bool = False
    
    async def connect(self):
        self.__bus = await MessageBus(self.bus_address, auth=AuthAnnonymous()).connect()
        _logger.info(f'Connected to new bus with address "{self.bus_address}" successfully.')

        # await attach_services_to_bus(self.__bus, wsl_distro_name=self.__distro_name)

    async def register_services(self):
        self.__bus.export('/org/freedesktop/Notifications', NotificationHandlerService(self.distro_name))
        await self.__bus.request_name('org.freedesktop.Notifications')

        media_control_service = MediaControlService(self.__bus, self.distro_name)
        await media_control_service.init_async()

        self.__is_ready = True

    # Blocking
    async def enter_loop_when_ready(self):
        """
        Enter loop (blocking) only when the connection is ready (e.g. services has been attached).

        Calling this function does not guarantee that the loop will start immediately; it is dependent on
        whether the connection is actually ready or not.
        """
        if self.__is_ready:
            await self.__bus.wait_for_disconnect()
        else:
            return False

    async def disconnect(self):
        self.was_manually_disconnected = True

        self.__bus.disconnect()

        # Sleep a little bit because we can't await the disconnect() method call.
        await asyncio.sleep(3)

        _logger.info(f'Disconnected from bus with address "{self.bus_address}".')

    def disconnect_sync(self):
        # FIXME: This is currently needed for the final clean-up function (before exiting the program).
        # There must be a better solution than using this separate method.

        self.was_manually_disconnected = True

        self.__bus.disconnect()
        _logger.info(f'Disconnected (without awaiting) from bus with address "{self.bus_address}".')

# Define FWSLBusConnection as global variable to simplify some logics.
fwsl_bus_connection: _FWSLBusConnection | None = None

# To indicate whether the program is about to exit (useful for stopping the main `while` loop in
# the main function).
exit_signal: bool = False

# def disconnect_any_connected_bus_factory(fbc: _FWSLBusConnection):
#     def disconnect_function():
#         fbc.disconnect()

#     return disconnect_function

# Define clean-up function before exiting the program.
def cleanup_before_exiting():
    _logger.info('Beginning clean-up...')

    # Put this here so that we won't encounter any unexpected things.
    global exit_signal
    exit_signal = True

    ToastNotificationManager.history.remove_group(NOTIFICATION_GROUP_NAME)
    _logger.info(f'Cleared all Windows ToastNotification with group name "{NOTIFICATION_GROUP_NAME}".')

    # bus_instance.disconnect()
    # global_disconnect()
    if fwsl_bus_connection is not None:
        fwsl_bus_connection.disconnect_sync()

    _logger.info('Clean-up complete.')


# async def connect_or_switch_to_distro(old_fbc: _FWSLBusConnection | None,
#                                       distro_name_for_new_bus: str) -> None:
# async def new_connection
async def connect_or_switch_to_distro(distro_name_for_new_bus: str) -> None:
    global fwsl_bus_connection

    try:
        new_fbc = _FWSLBusConnection(distro_name_for_new_bus)
        await new_fbc.connect()
    except RuntimeError:
        _logger.error(f'Cannot connect to "{distro_name_for_new_bus}". ' +
                      ('The former bus connection is still preserved.'
                       if fwsl_bus_connection is not None else ''))
        # return old_fbc
    
    # if old_fbc is not None:
    #     await old_fbc.disconnect()
    if fwsl_bus_connection is not None:
        await fwsl_bus_connection.disconnect()

    await new_fbc.register_services()

    # Attach to global disconnect function.
    # global global_disconnect
    # global_disconnect = disconnect_any_connected_bus_factory(new_fbc)

    fwsl_bus_connection = new_fbc

    # return new_fbc
        

async def fwsl_daemon(tray_icon: PersistentTrayIcon):
    # nonlocal current_bus_address

    # Do checks first
    try:
        preliminary_checks()
    except RuntimeError as e:
        _logger.error(e.args[0])
        sys.exit(1)

    # _logger.info('Starting FancyWSL Daemon...')

    # default_distro_name = [item for item in state['distro_list'] if item['is_default'] == True][0]['name']
    # default_distro_name = 'Ubuntu'



    try:
        # fbc = FWSLBusConnection(default_distro_name)
        # while fbc == None:
        #     fbc = connect_or_switch_to_distro(None, default_distro_name)
        #     await fbc.enter_loop()

        # _logger.info('Connected to bus successfully.')
        while exit_signal == False:            
            if fwsl_bus_connection is None or not fwsl_bus_connection.was_manually_disconnected:
                _logger.info('Attempting to connect to the default WSL distribution...')

                # global fwsl_bus_connection
                # fwsl_bus_connection = FWSLBusConnection(default_distro_name)
                refresh_distro_list()

                try:
                    default_distro_name = [item for item in distro_list if item['is_default']][0]['name']
                except IndexError:
                    continue

                await connect_or_switch_to_distro(default_distro_name)

            # Wait five seconds on each loop unless it is the first run.
            if fwsl_bus_connection is not None:
                await asyncio.sleep(5)
            
            await fwsl_bus_connection.enter_loop_when_ready()
    except Exception as e:
        _logger.error('Some error happened. Exiting FancyWSL Daemon...')
        tray_icon.t__icon_instance.stop()
        raise e
        # sys.exit(1)

    # await attach_services_to_bus(bus, wsl_distro_name=platform_info['wsl_distro_name'])


    # def persistent_tray_icon_quit_handler(_):
    #     _logger.info('Received quit request.')
    #     cleanup_before_exiting(bus_instance=bus)
    #     _logger.info('Killed the system tray icon.')

    # This is the main blocking call.
    # await bus.wait_for_disconnect()

    # This portion will be reached when the bus is disconnected.
    # _logger.info(f'Connection to bus "{bus_address}" disconnected.')
    # _logger.info('Exiting FancyWSL Daemon...')

# The program entry point.
def main():
    argument_parser = ArgumentParser('FancyWSL Daemon')
    argument_parser.add_argument('--verbose', help='Print more logs verbosely.', action='store_true')
    args = argument_parser.parse_args()

    # Set up logging.
    log_level = logging.WARNING if args.verbose is None else logging.INFO
    logging.basicConfig(format='FWSL LOG | %(asctime)s | (%(name)s) %(levelname)s: %(message)s',
                        level=log_level)
    
    global _logger
    _logger = logging.getLogger(__name__)

    # state: CurrentState = {'distro_list': []}
                        #    'current_bus_address': None}
    
    # def populate_distro_list():
    #     query_result = get_wsl_distro_list()
    #     # is_distro_currently_active = lambda distro_name: fwsl_bus_connection if fwsl_bus_connection

    #     print(query_result)

    #     # def check_if_distro_is_currently_active(distro_name: str):
    #     #     if fwsl_bus_connection is not None:
    #     #         return distro_name == fwsl_bus_connection.distro_name
    #     #     return False
        
    #     state['distro_list'] = [{'name': item['name'],
    #                              'is_default': item['is_default']}
    #                             #  'is_chosen': check_if_distro_is_currently_active(item['name'])}
    #                             for item in query_result]
        
        # print(query_result)
    
    # def distro_list_value_getter():
    #     # Run each time the values are requested for good measure.
    #     populate_distro_list()

    #     distro_list = state['distro_list']
    #     print('a')
    #     print(distro_list)
    #     if len(distro_list) != 0:
    #         return distro_list
        
    #     return None

    # def get_distro_list_value_for_tray_icon

    def refresh_and_get_distro_list():
        refresh_distro_list()
        return distro_list

    tray_icon = PersistentTrayIcon(refresh_and_get_distro_list,
                                #    lambda: state['current_bus_address'],
                                   connect_or_switch_to_distro,
                                   cleanup_before_exiting)

    # Workaround because we're running on Windows (instead of Unix-like/Linux).
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Run main loop
    asyncio.get_event_loop().run_until_complete(fwsl_daemon(tray_icon))

    # The main loop will autmatically end when the bus has disconnected.
    

if __name__ == '__main__':
    main()
