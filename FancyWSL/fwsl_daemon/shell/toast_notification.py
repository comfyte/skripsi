from winsdk.windows.ui import notifications
from winsdk.windows.data.xml import dom
import sys

class WindowsToastNotification():
    def __init__(self) -> None:
        self.notifier = notifications.ToastNotificationManager.create_toast_notifier()
        self.raw_markup = """
<toast duration='short'>
    <visual>
        <binding template='ToastGeneric'>
            <text>Notifikasi baru</text>
            <text>Teks</text>
            <text>Teks kedua</text>
        </binding>
    </visual>
</toast>
"""
        xml_document = dom.XmlDocument()
        xml_document.load_xml(self.raw_markup)
        self.toast_notification = notifications.ToastNotification(xml_document)

        self.toast_notification.add_activated(sys.exit)

    def display(self) -> None:
        print(self.toast_notification)
        self.notifier.show(self.toast_notification)
