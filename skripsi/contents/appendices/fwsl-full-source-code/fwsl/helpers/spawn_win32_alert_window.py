import ctypes
import logging

_logger = logging.getLogger('win32_alert_window')

def spawn_win32_alert_window(title: str, message_body: str, type: str = 'basic'):
    if type != 'basic':
        raise NotImplementedError()
    
    _logger.info(f'A Win32 alert window with title "{title}" has been spawned.')
    result =  ctypes.windll.user32.MessageBoxW(None, message_body, title, 0)
    _logger.info(f'The Win32 alert window with title "{title}" has been closed with result "{result}".')
    return result
