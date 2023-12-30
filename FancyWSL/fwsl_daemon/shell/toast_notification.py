from winsdk.windows.ui import notifications
from winsdk.windows.data.xml import dom
from xml.sax.saxutils import escape as xml_escape
from ..helpers.constants import NOTIFICATION_GROUP_NAME

class WindowsToastNotification():
    def __init__(self,
                 wsl_distro_name: str,
                 *,
                 app_name: str = None,
                 id: int = None,
                 title: str = None,
                 body_content: str,
                 expire_timeout: int) -> None:
        self.notifier = notifications.ToastNotificationManager.create_toast_notifier()

        # The very first line of the <text> element is apparently treated as the title of
        # the notification.
        self.raw_markup = f"""
<toast duration='short'>
    <visual>
        <binding template='ToastGeneric'>
            {f'<text>{xml_escape(title)}</text>' if title is not None else ''}
            <text placement='attribution'>{f'{xml_escape(app_name)} on' if app_name is not None else 'From'} {xml_escape(wsl_distro_name)} (WSL)</text>
            <text>{xml_escape(body_content)}</text>
        </binding>
    </visual>
</toast>
"""
        xml_document = dom.XmlDocument()
        xml_document.load_xml(self.raw_markup)
        self.toast_notification = notifications.ToastNotification(xml_document)

        self.toast_notification.expires_on_reboot = True

        # group_name = f'{(app_name + " on ") if app_name is not None else ""}{wsl_distro_name} (WSL)'
        # self.toast_notification.group = group_name

        # self.toast_notification.expiration_time = 

        # self.toast_notification.tag = 'halodunia'

        # Apparently, group names are not for visual distinction, but rather just kind of internal IDs.
        self.toast_notification.group = NOTIFICATION_GROUP_NAME

        self.toast_notification.add_activated(self.__activation_handler)

    def display(self) -> None:
        self.notifier.show(self.toast_notification)

    def __activation_handler(self, sender, args):
        print(type(sender))
        print(type(args))
