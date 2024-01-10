import logging
import platform
import subprocess
from subprocess import CalledProcessError
from .wsl_manager import wsl_get_version, wsl_get_distro_list

# Get logger for current module
logger = logging.getLogger(__name__)

def _verify_proper_os() -> None:
    if platform.system() != 'Windows':
        if platform.system() == 'Linux' and (platform.uname().release.endswith('-Microsoft') or
                                             platform.uname().release.endswith('microsoft-standard-WSL')):
            raise RuntimeError('This program needs to be launched in a Windows environment, not inside WSL.')
        else:
            raise RuntimeError('This program is designed to bridge Windows and WSL; hence, it needs to run '
                               'on Windows. Running this program on non-Windows platforms is not supported.')
            
def _verify_wsl_availability() -> None:
    try:
        wsl_get_version()
    except CalledProcessError:
        raise RuntimeError('An error occured. Either WSL is not installed, the installed WSL doesn\'t come '
                           'with `wsl.exe` command yet, or there is an error executing `wsl.exe`. Either '
                           'way, please ensure that WSL is installed on this system (the Microsoft Store '
                           'edition is preferred).')
    
def verify_wsl_distro_readiness(distro_name: str) -> None:
    try:
        subprocess.run(['wsl.exe', '-d', distro_name, '[', '-d', '/run/systemd/system', ']'], check=True)
    except CalledProcessError:
        raise RuntimeError('The selected WSL distribution is not booted with systemd. Enable systemd in '
                           'the WSL configuration in order to use FancyWSL.')
    
    try:
        # TODO: The check needs to be much more than just this.
        subprocess.run(['wsl.exe', '-d', distro_name, '[', '-f', '/etc/dbus-1/session-local-fwsl.conf', ']'],
                       check=True)
    except CalledProcessError as e:
        # Do we even need to check this?
        if e.returncode != 0:
            raise RuntimeError(f'The distribution "{distro_name}" is not configured to work with FancyWSL '
                               'yet; cannot switch to it.')
        
        # Else
        raise e

def preliminary_checks() -> None:
    _verify_proper_os()
    _verify_wsl_availability()
