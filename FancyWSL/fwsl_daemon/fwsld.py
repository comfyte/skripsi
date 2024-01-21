from logging import getLogger
from asyncio import create_task, CancelledError

from .shell.persistent_tray_icon import PersistentTrayIcon
from .distro_prober import distro_prober

class FancyWSLDaemon:
    def __init__(self) -> None:
        self.__logger = getLogger('fwsld')
        self.__persistent_tray_icon = PersistentTrayIcon(exit_callback=self.__cleanup_before_exit)

    def __cleanup_before_exit(self, _):
        self.__main_task.cancel()

    # Blocking (until the daemon is exited, presumably via the tray icon)
    async def start(self) -> None:
        main_coroutine = distro_prober(self.__persistent_tray_icon.set_distro_connection_count)
        self.__main_task = create_task(main_coroutine)

        try:
            await self.__main_task
        except CancelledError:
            self.__logger.info('The main daemon task has been cancelled.')
