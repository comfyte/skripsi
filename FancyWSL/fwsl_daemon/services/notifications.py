import logging
from dbus_next.aio import MessageBus
from dbus_next.service import (ServiceInterface, method,
                               dbus_property, signal)
from dbus_next import Variant, DBusError
from ..shell.toast_notification import (show_windows_toast_notification,
                                        close_windows_toast_notification,
                                        ToastDismissalReason)

# Get logger for current module
_logger = logging.getLogger(__name__)

class NotificationHandlerService(ServiceInterface):
    def __init__(self, wsl_distro_name: str):
        super().__init__('org.freedesktop.Notifications')

        self.wsl_distro_name = wsl_distro_name
    
    @method()
    def GetCapabilities(self) -> 'as':
        return ['body', 'actions']
    
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
        actions_parsed = [(actions[i], actions[i+1]) for i in range(0, len(actions), 2) if
                          actions[i] != 'default']

        id = show_windows_toast_notification(self.wsl_distro_name,
                                             app_name=app_name,
                                             id=replaces_id,
                                             title=summary,
                                             body_content=body,
                                             actions=actions_parsed,
                                             expire_timeout=expire_timeout,
                                             activated_callback=self.ActionInvoked,
                                             dismiss_callback=self.notification_dismissed_handler)
        
        return id
    
    @method()
    def CloseNotification(self, id: 'u') -> None:
        close_windows_toast_notification(id)

    @method()
    def GetServerInformation(self) -> 'ssss':
        return ['FancyWSL Notification Server',
                'Independent',
                '0.0.1',
                '1.2']
    
    @signal()
    def ActionInvoked(self, notification_id: int, action_key: str) -> 'us':
        _logger.info('An ActionInvoked signal is sent.')
        return [notification_id, action_key]
    
    @signal()
    def NotificationClosed(self, notification_id: int, reason: int) -> 'uu':
        _logger.info(f'A NotificationClosed signal is sent for notification with ID {notification_id} and '
                     f'with reason number {reason}.')
        return [notification_id, reason]
    
    def notification_dismissed_handler(self, notification_id: int, win_reason: ToastDismissalReason) -> None:
        if win_reason == ToastDismissalReason.USER_CANCELED:
            xdg_reason = 2
        else:
            # Not implemented yet (TODO).
            return
        
        self.NotificationClosed(notification_id, xdg_reason)

    def post_notification_closed_by_dbus_method_call_handler(self, notification_id: int):
        self.NotificationClosed(notification_id, 3)
