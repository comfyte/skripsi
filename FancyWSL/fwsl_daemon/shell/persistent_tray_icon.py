from infi.systray import SysTrayIcon

class PersistentTrayIcon():
    def __init__(self, exit_callback) -> None:
        # TODO: Check first if the exit_callback function is properly given and properly exists

        self.instance = SysTrayIcon('../assets/app-icon.png', 'FancyWSL Daemon', on_quit=exit_callback)
        self.instance.start()
        print('Summoned the system tray icon')
