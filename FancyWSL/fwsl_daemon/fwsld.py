from logging import Logger, getLogger
from asyncio import create_task, Task, CancelledError

from .shell.persistent_tray_icon import PersistentTrayIcon
from .distro_prober import distro_prober

_logger: Logger
_main_task: Task
_persistent_tray_icon: PersistentTrayIcon

def _cleanup_before_exit(*args):
    _logger.info('Received exit request from user. Will exit in a moment...')
    _main_task.cancel()

# Blocking (until the daemon is exited, presumably via the tray icon)
async def start() -> None:
    global _logger, _main_task, _persistent_tray_icon

    # Initialize the global variables.
    _logger = getLogger('fwsld')
    _persistent_tray_icon = PersistentTrayIcon(exit_callback=_cleanup_before_exit)
    
    main_coroutine = distro_prober(_persistent_tray_icon.set_distro_connection_count)
    _main_task = create_task(main_coroutine)

    try:
        await _main_task
    except CancelledError:
        _logger.info('The main daemon task has been cancelled.')
