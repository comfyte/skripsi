import ctypes

def spawn_win32_alert_window(title: str, message_body: str, type: str):
    if type != 'error':
        raise NotImplementedError()
    
    return ctypes.windll.user32.MessageBoxW(None, message_body, title, 0)
