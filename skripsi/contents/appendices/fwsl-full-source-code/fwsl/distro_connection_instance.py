from logging import getLogger
from typing import Callable
from asyncio import CancelledError
from dbus_next.aio import MessageBus
from dbus_next.auth import AuthAnnonymous
from .helpers.platform_verifications import wsl_distro_verification
from .services.notifications import NotificationHandlerService
from .services.mpris import MediaControlService
from .helpers.obtain_bus_address import obtain_bus_address
from .shell.toast_notification import clear_all_windows_toast_notifications_for_specific_distro
from .helpers.exceptions import DistroUnsupportedError

class DistroConnectionInstance:
    """
    Make sure to call the `connect()` method first before doing any other operation.
    """
    def __init__(self, distro_name, completion_callback: Callable[[str], None] = None) -> None:
        self.distro_name = distro_name

        if not wsl_distro_verification.is_distro_ready(distro_name):
            raise DistroUnsupportedError

        try:
            obtained_bus_address = obtain_bus_address(distro_name)
        except ValueError:
            raise DistroUnsupportedError
        
        self.bus_address = obtained_bus_address['full_address']
        self.__logger = getLogger(distro_name)
        self.__completion_callback = completion_callback

    def __hash__(self) -> int:
        return hash(self.distro_name)
    
    def __eq__(self, other: object) -> bool:
        return self.distro_name == other.distro_name

    async def connect(self) -> None:
        self.__bus_instance = MessageBus(self.bus_address, auth=AuthAnnonymous())
        await self.__bus_instance.connect()

        self.__logger.info('Connected.')

        # Name ourselves in the message bus.
        await self.__bus_instance.request_name('dev.farrel.FancyWSL')

        await self.__attach_services()
        
    async def __setup_notification_service(self) -> None:
        # Assign an additional name to ourselves to designate ourselves as the (sole) notification handler
        # service in the message bus.
        await self.__bus_instance.request_name('org.freedesktop.Notifications')

        self.__bus_instance.export('/org/freedesktop/Notifications',
                                   NotificationHandlerService(self.distro_name))
        
    async def __setup_media_control_service(self) -> None:
        media_control_service = MediaControlService(self.__bus_instance, self.distro_name)
        await media_control_service.attach()

    async def __attach_services(self) -> None:
        await self.__setup_notification_service()
        await self.__setup_media_control_service()
        self.__logger.info('Services have been attached.')

    def __post_disconnection(self) -> None:
        clear_all_windows_toast_notifications_for_specific_distro(self.distro_name)

        if self.__completion_callback is not None:
            self.__completion_callback()

    async def enter_loop(self) -> None:
        self.__logger.info('Entered loop.')

        try:
            # Blocking
            await self.__bus_instance.wait_for_disconnect()

        # If the bus disconnects by itself
        except EOFError:
            # FIXME
            self.__logger.warn('Ignored an EOFError exception.')
        # If cancelled by user
        except CancelledError:
            self.__logger.info('The loop has been cancelled.')

            # Check if the bus is still connected.
            if self.__bus_instance.connected:
                self.__logger.info('Bus is still connected. Disconnecting...')
                self.__bus_instance.disconnect()
                self.__logger.info('Bus has been disconnected.')
            raise
        finally:
            self.__logger.info('Bus disconnection ended the loop.')
            self.__post_disconnection()

    def disconnect_manually(self) -> None:
        """
        Note: This will still call the `completion_callback()` function you have provided, so
        do not call that function separately (e.g. in the line below where you called
        this `disconnect_manually()` method).
        """
        self.__bus_instance.disconnect()
