import logging
from typing import Callable
from winsdk.windows.ui.notifications import (ToastNotificationManager,
                                             ToastNotification,
                                             ToastActivatedEventArgs,
                                             ToastDismissedEventArgs,
                                             ToastDismissalReason)
from winsdk.windows.data.xml import dom
from xml.sax.saxutils import escape as xml_escape
from ..helpers.unbox_winrt_object import unbox_winrt_object, WinRTObject
from ..helpers.constants import NOTIFICATION_GROUP_NAME

# Get logger for current module
_logger = logging.getLogger(__name__)

_toast_notifier = ToastNotificationManager.create_toast_notifier()

_notification_id_counter: int = 1

def show_windows_toast_notification(wsl_distro_name: str,
                                    *,
                                    app_name: str = '',
                                    id: int,
                                    title: str = '',
                                    body_content: str,
                                    actions: list[tuple[str, str]] = None, #TODO
                                    expire_timeout: int,
                                    activated_callback: Callable,
                                    dismiss_callback: Callable) -> int:
    
    # Is hardcoding the "default" launch argument the proper way?
    markup_string = f"""
<toast duration='short' launch='default'>
    <visual>
        <binding template='ToastGeneric'>
            {f'<text>{xml_escape(title)}</text>' if title != '' else ''}
            <text placement='attribution'>{f'{xml_escape(app_name)} on' if app_name != '' else 'From'} {xml_escape(wsl_distro_name)} (WSL)</text>
            <text>{xml_escape(body_content)}</text>
        </binding>
    </visual>

{f'''
    <actions>
        {''.join([f'<action content="{xml_escape(text)}" activationType="foreground" arguments="{xml_escape(identifier)}" />' for (identifier, text) in actions])}
    </actions>
 ''' if actions is not None else ''}
</toast>
"""
        
    xml_document = dom.XmlDocument()
    xml_document.load_xml(markup_string)

    toast_notification = ToastNotification(xml_document)

    toast_notification.expires_on_reboot = True

    # Apparently, group names are not for visual distinction, but rather just kind of internal IDs.
    toast_notification.group = NOTIFICATION_GROUP_NAME

    if id == 0:
        global _notification_id_counter
        id_new = _notification_id_counter
        _notification_id_counter += 1
    else:
        id_new = id
        ToastNotificationManager.history.remove(str(id_new), NOTIFICATION_GROUP_NAME)

    # tag = str(_id)

    # Remove notification with existing same id first.
    # ToastNotificationManager.history.remove(tag)

    toast_notification.tag = str(id_new)

    def activation_handler(sender: ToastNotification, args):
        activation_argument = ToastActivatedEventArgs._from(args).arguments
        _logger.info(f'Received an activation event from notification with ID/tag {sender.tag} and '
                     f'argument (action key) "{activation_argument}".')
        activated_callback(id_new, activation_argument)
        # print(ToastActivatedEventArgs._from(args).arguments)

    def dismiss_handler(sender: ToastNotification, _args):
        args = ToastDismissedEventArgs._from(_args)
        _logger.info(f'Toast notification with ID/tag "{sender.tag}" was dismissed with '
                     f'reason (ToastDismissalReason) number {args.reason}.')
        dismiss_callback(id_new, args.reason)

    toast_notification.add_activated(activation_handler)
    toast_notification.add_dismissed(dismiss_handler)

    _toast_notifier.show(toast_notification)

    return id_new

def close_windows_toast_notification(id: int, post_removal_callback: Callable):
    ToastNotificationManager.history.remove(str(id), NOTIFICATION_GROUP_NAME)

    # Do we need to do this or will a signal automatically emitted by the toast notification?
    post_removal_callback(id)

# __all__ = ['show_windows_toast_notification']
