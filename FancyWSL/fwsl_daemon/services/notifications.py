from dbus_next.aio import MessageBus
from dbus_next.service import (ServiceInterface, method,
                               dbus_property, signal)
from dbus_next import Variant, DBusError

from ..shell.toast_notification import WindowsToastNotification

class NotificationHandlerService(ServiceInterface):
    def __init__(self):
        super().__init__('org.freedesktop.Notifications')
        # self.notification_manager = win_ui_notifications.ToastNotificationManager()
    
    @method()
    def GetCapabilities(self):
        print('GC called')
        # return [
        #     'body'
        # ]
    
    @method()
    def Notify(self, app_name: 's', replaces_id: 'u', app_icon: 's',
               summary: 's', body: 's', actions: 'as', hints: 'a{sv}', expire_timeout: 'i') -> 'u':
        print('N called')

        print(app_name)
        print(replaces_id)
        print(app_icon)
        print(summary)
        print(body)
        print(actions)
        print(hints)
        print(expire_timeout)

        print(type(body))

        wtn = WindowsToastNotification()
        wtn.display()

        if replaces_id == 0:
            return 3925
        else:
            return replaces_id

    @method()
    def GetServerInformation(self) -> 'ssss':
        print('GSC called')

        return [
            'FancyWSL Notification Server',
            'Independent',
            '0.0.1',
            '1.2'
        ]
    