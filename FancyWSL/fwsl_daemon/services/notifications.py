from dbus_next.aio import MessageBus
from dbus_next.service import (ServiceInterface, method,
                               dbus_property, signal)
from dbus_next import Variant, DBusError

from ..shell.toast_notification import WindowsToastNotification

class NotificationHandlerService(ServiceInterface):
    def __init__(self, wsl_distro_name: str):
        super().__init__('org.freedesktop.Notifications')

        self.wsl_distro_name = wsl_distro_name
    
    @method()
    def GetCapabilities(self):
        # Turns out that this isn't really needed, but still FIXME.
        pass
    
    @method()
    def Notify(self,
               app_name: 's',
               replaces_id: 'u',
               app_icon: 's',
               summary: 's',
               body: 's',
               actions: 'as',
               hints: 'a{sv}',
               expire_timeout: 'i') -> 'u':
        windows_toast_notification = WindowsToastNotification(self.wsl_distro_name,
                                                              app_name=app_name,
                                                              id=replaces_id,
                                                              title=summary,
                                                              body_content=body,
                                                              expire_timeout=expire_timeout)
        windows_toast_notification.display()

    @method()
    def GetServerInformation(self) -> 'ssss':
        return [
            'FancyWSL Notification Server',
            'Independent',
            '0.0.1',
            '1.2'
        ]
    