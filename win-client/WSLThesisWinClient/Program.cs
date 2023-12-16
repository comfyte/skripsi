using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Drawing;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
using Windows.Media;
using Windows.Media.Playback;
using FWSLHostBridge.Services;
using FWSLHostBridge.Helpers;
using Tmds.DBus;

namespace FWSLHostBridge
{
    internal class App : ApplicationContext
    {
        private SysTrayIconManager _sysTrayIconManager;

        public App()
        {
            _sysTrayIconManager = new SysTrayIconManager();
            new MPRISControl();

            var busConnection = Tmds.DBus.Protocol.Connection.
        }
    }

    static class Program
    {
        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);

            Application.Run(new App());
        }
    }
}