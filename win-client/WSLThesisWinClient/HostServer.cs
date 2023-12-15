using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.Hosting;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace FWSLHostBridge
{
    internal class HostServer
    {
        private WebApplication _server;

        public HostServer()
        {
            _server = WebApplication.Create();
            _server.Map("/", () => "Mencoba");
            _server.Start();
        }
    }
}
