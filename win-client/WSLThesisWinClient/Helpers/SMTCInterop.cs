using System;
using System.Collections.Generic;
using System.Text;
using System.Runtime.InteropServices.WindowsRuntime;
using Windows.Media;

namespace FWSLHostBridge.Helpers
{
    public static class SMTCInterop
    {
        public static SystemMediaTransportControls GetForWindow(IntPtr hWnd)
        {
            ISMTCInterop smtcInterop = (ISMTCInterop)WindowsRuntimeMarshal.GetActivationFactory(typeof(SystemMediaTransportControls));
            Guid guid = typeof(SystemMediaTransportControls).GUID;

            return smtcInterop.GetForWindow(hWnd, ref guid);
        }
    }

    [System.Runtime.InteropServices.Guid("ddb0472d-c911-4a1f-86d9-dc3d71a95f5a")]
    [System.Runtime.InteropServices.InterfaceType(System.Runtime.InteropServices.ComInterfaceType.InterfaceIsIInspectable)]
    interface ISMTCInterop
    {
        SystemMediaTransportControls GetForWindow(IntPtr appWindow, [System.Runtime.InteropServices.In] ref Guid riid);
    }
}
