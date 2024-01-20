from logging import getLogger
from asyncio import create_task, CancelledError

from .shell.persistent_tray_icon import PersistentTrayIcon
from .distro_prober import distro_prober

class FancyWSLDaemon:
    def __init__(self) -> None:
        self.__logger = getLogger('fwsld')
        self.__persistent_tray_icon = PersistentTrayIcon(exit_callback=self.__cleanup_before_exit)

    # def handle_exit
    def __cleanup_before_exit(self, _):
        # pass
        # try:
        self.__main_task.cancel()
        # except CancelledError:
        #     self.__logger.info('A CancelledError exception is received.')

    # Blocking (until the daemon is exited, presumably via the tray icon)
    async def start(self) -> None:
        # await distro_prober(lambda new_value: self.__persistent_tray_icon.distro_connection_count = new_value)
        # pass
        main_coroutine = distro_prober(self.__persistent_tray_icon.set_distro_connection_count)
        self.__main_task = create_task(main_coroutine)

        try:
            await self.__main_task
        except CancelledError:
            # self.__logger.info('A CancelledError exception is received.')
            self.__logger.info('The main daemon task has been cancelled.')
