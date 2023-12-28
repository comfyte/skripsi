import logging
from infi.systray import SysTrayIcon

# Get logger for current module
logger = logging.getLogger(__name__)

class PersistentTrayIcon():
    def __init__(self, bus_address: str, exit_callback) -> None:
        # TODO: Check first if the exit_callback function is properly given and properly exists

        # menu_items = (('FancyWSL (Bridging WSL and Windows)', None, None),
        #               (f'Connected to D-Bus session bus at "{bus_address}"', None, None))

        self.instance = SysTrayIcon(None, f'FancyWSL Daemon (Connected to "{bus_address}")',
                                    on_quit=exit_callback)
        self.instance.start()
        logger.info('Summoned the system tray icon')
