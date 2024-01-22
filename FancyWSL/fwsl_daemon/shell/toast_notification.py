from logging import getLogger
from typing import Callable
from winsdk.windows.ui.notifications import (ToastNotificationManager,
                                             ToastNotification,
                                             ToastActivatedEventArgs,
                                             ToastDismissedEventArgs)
from winsdk.windows.data.xml import dom
from xml.sax.saxutils import escape as xml_escape

_COMMON_GROUP_NAME = 'FancyWSL Notifications'

def _get_group_name(distro_name: str):
    return f'{_COMMON_GROUP_NAME} ({distro_name})'

_toast_notifier = ToastNotificationManager.create_toast_notifier()

_notification_id_counter: int = 1

def show_windows_toast_notification(distro_name: str,
                                    *,
                                    app_name: str = '',
                                    _id: int,
                                    title: str = '',
                                    body_content: str,
                                    actions: list[tuple[str, str]] = None, #TODO
                                    expire_timeout: int,
                                    activated_callback: Callable,
                                    dismiss_callback: Callable) -> int:
    logger = getLogger(f'toast_notification.{distro_name}')
    
    # Is hardcoding the "default" launch argument the proper way?
    markup_string = f"""
<toast duration='short' launch='default'>
    <visual>
        <binding template='ToastGeneric'>
            {f'<text>{xml_escape(title)}</text>' if title != '' else ''}
            <text placement='attribution'>{f'{xml_escape(app_name)} on' if app_name != '' else 'From'} {xml_escape(distro_name)} (WSL)</text>
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

    group_name = _get_group_name(distro_name)

    # Apparently, group names are not for visual distinction, but rather just kind of internal IDs.
    toast_notification.group = group_name

    if _id == 0:
        global _notification_id_counter
        id = _notification_id_counter
        _notification_id_counter += 1
    else:
        id = _id
        ToastNotificationManager.history.remove(str(id), group_name)

    # Remove notification with existing same id first.
    # ToastNotificationManager.history.remove(tag)

    toast_notification.tag = str(id)

    def activation_handler(sender: ToastNotification, args):
        activation_argument = ToastActivatedEventArgs._from(args).arguments
        logger.info(f'Received an activation event from notification with ID/tag {sender.tag} and '
                    f'argument (action key) "{activation_argument}".')
        activated_callback(id, activation_argument)

    def dismiss_handler(sender: ToastNotification, _args):
        args = ToastDismissedEventArgs._from(_args)
        logger.info(f'Toast notification with ID/tag "{sender.tag}" was dismissed with '
                    f'reason (ToastDismissalReason) number {args.reason}.')
        dismiss_callback(id, args.reason)

    toast_notification.add_activated(activation_handler)
    toast_notification.add_dismissed(dismiss_handler)

    _toast_notifier.show(toast_notification)

    return id

def close_windows_toast_notification(id: int, distro_name: str, post_removal_callback: Callable):
    ToastNotificationManager.history.remove(str(id), _get_group_name(_COMMON_GROUP_NAME, distro_name))

    # Do we need to do this or will a signal automatically emitted by the toast notification?
    post_removal_callback(id)

def clear_all_windows_toast_notifications_for_specific_distro(distro_name: str):
    ToastNotificationManager.history.remove_group(_get_group_name(distro_name))
