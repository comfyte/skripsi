using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Windows.Media.Playback;
using Windows.Media;

namespace FWSLHostBridge.Services
{
    internal class MPRISControl
    {
        private MediaPlayer _mediaPlayer;
        private SystemMediaTransportControls _controls;
        private SystemMediaTransportControlsDisplayUpdater _updater;

        private void _initSmtc()
        {
            _mediaPlayer = new MediaPlayer();
            _controls = _mediaPlayer.SystemMediaTransportControls;
            _mediaPlayer.CommandManager.IsEnabled = false;

            _updater = _controls.DisplayUpdater;

            _controls.IsEnabled = true;
            // _controls.PlaybackStatus = MediaPlaybackStatus.Playing;

            _controls.IsPlayEnabled = true;
            _controls.IsPauseEnabled = true;
            _controls.IsNextEnabled = true;
            _controls.IsPreviousEnabled = true;
        }

        public MPRISControl()
        {
            _initSmtc();
        }
    }
}
