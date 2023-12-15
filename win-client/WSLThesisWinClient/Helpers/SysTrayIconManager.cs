// For enabling the persistent "system tray" icon

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace FWSLHostBridge.Helpers
{
    internal class SysTrayIconManager
    {
        private readonly NotifyIcon _sysTrayIcon;

        public SysTrayIconManager()
        {
            _sysTrayIcon = new NotifyIcon
            {
                Text = "WSL Extended Shell Integration",
                Icon = new Icon(SystemIcons.Application, 32, 32), // TODO: Change the icon to something saner
                ContextMenuStrip = new ContextMenuStrip(),
                Visible = true
            };

            _sysTrayIcon.ContextMenuStrip.Items.Add(new ToolStripMenuItem("Keluar", null, _exitApp));

        }

        private void _cleanUp()
        {
            _sysTrayIcon.Visible = false;
        }

        private void _exitApp(object sender, EventArgs e)
        {
            _cleanUp();
            Application.Exit();
        }
    }
}
