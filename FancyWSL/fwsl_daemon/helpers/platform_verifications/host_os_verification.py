import platform
import subprocess
from subprocess import CalledProcessError

# def _is_os_correct() -> tuple(False, str) | tuple(True):
# def _is_os_correct() -> tuple[False, str] | tuple[True]:
def _os_check() -> tuple[bool, str]:
    if platform.system() != 'Windows':
        if platform.system() == 'Linux' and (platform.uname().release.endswith('-Microsoft') or
                                             platform.uname().release.endswith('microsoft-standard-WSL')):
            # raise RuntimeError('This program needs to be launched in a Windows environment, not inside WSL.')
            # return (False, 'Running inside WSL')
            # return (False, 'inside WSL')
            return (False, 'WSL guest')
        else:
            # raise RuntimeError('This program is designed to bridge Windows and WSL; hence, it needs to run '
            #                    'on Windows. Running this program on non-Windows platforms is not supported.')
            # return (False, 'Non-Windows platform')
            return (False, 'Non-Windows')
    
    # return (True, 'Windows')
    return (True, 'Windows host')
            
def _is_wsl_installed() -> bool:
    # Check availability of the WSL itself
    try:
        # The top answer in https://stackoverflow.com/a/19328914 says that the output we'll get is
        # encoded in UTF-16-LE (likely because this is a Windows console/shell output), so we'll
        # specify that encoding information here.
        subprocess.run(['wsl.exe', '--version'], check=True, capture_output=True, encoding='utf-16-le')
    except CalledProcessError:
        # raise RuntimeError('An error occured. Either WSL is not installed, the installed WSL doesn\'t come '
        #                    'with `wsl.exe` command yet, or there is an error executing `wsl.exe`. Either '
        #                    'way, please ensure that WSL is installed on this system (the Microsoft Store '
        #                    'edition is preferred).')
        # return (False, 'Error in running the "wsl.exe --version" command')
        return False
    
    return True


def check_all() -> None:
    """
    Can raise a `RuntimeError` exception.
    """
    # if not all([_os_check()[0], _is_wsl_installed()]):
    #     raise RuntimeError('Platform not supported')
    if not _os_check()[0]:
        raise RuntimeError('Not running on Windows')
    
    if not _is_wsl_installed():
        raise RuntimeError('WSL is not installed')
