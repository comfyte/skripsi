import platform
import subprocess
from subprocess import CalledProcessError

def _os_check() -> tuple[bool, str]:
    if platform.system() != 'Windows':
        if platform.system() == 'Linux' and (platform.uname().release.endswith('-Microsoft') or
                                             platform.uname().release.endswith('microsoft-standard-WSL')):
            return (False, 'WSL guest')
        else:
            return (False, 'Non-Windows')
    
    return (True, 'Windows host')
            
def _is_wsl_installed() -> bool:
    # Check availability of the WSL itself.
    try:
        subprocess.run(['wsl.exe', '--version'], check=True, capture_output=True, encoding='utf-16-le')
    except CalledProcessError:
        return False
    
    return True


def check_all() -> None:
    """
    Can raise a `RuntimeError` exception.
    """
    if not _os_check()[0]:
        raise RuntimeError('Not running on Windows')
    
    if not _is_wsl_installed():
        raise RuntimeError('WSL is not installed')
