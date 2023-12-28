from winsdk.windows.ui import notifications
from winsdk.windows.data.xml import dom
import sys

class WindowsToastNotification():
    def __init__(self, app_name: str, title: str, body_content: str) -> None:
        self.notifier = notifications.ToastNotificationManager.create_toast_notifier()

        # The very first line of the <text> element is apparently treated as the title of
        # the notification.
        self.raw_markup = f"""
<toast duration='short'>
    <visual>
        <binding template='ToastGeneric'>
            <text>(WSL{f': {app_name or ""}'}){f' {title or ""}'}</text>
            <text>{body_content}</text>
        </binding>
    </visual>
</toast>
"""
        xml_document = dom.XmlDocument()
        xml_document.load_xml(self.raw_markup)
        self.toast_notification = notifications.ToastNotification(xml_document)

        self.toast_notification.add_activated(self.__activation_handler)

    def display(self) -> None:
        print(self.toast_notification)
        self.notifier.show(self.toast_notification)

    def __activation_handler(self, sender, args):
        print(sender.content)
        print(sender.data)
        print(sender.tag)
        print(sender.suppress_popup)

        print(dir(args))
