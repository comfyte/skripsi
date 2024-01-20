import logging
import platform
import subprocess
from subprocess import CalledProcessError

from .exceptions import DistroUnsupportedError

# Get logger for current module
logger = logging.getLogger(__name__)

def _verify_proper_os():
    if platform.system() != 'Windows':
        if platform.system() == 'Linux' and (platform.uname().release.endswith('-Microsoft') or
                                             platform.uname().release.endswith('microsoft-standard-WSL')):
            raise RuntimeError('This program needs to be launched in a Windows environment, not inside WSL.')
        else:
            raise RuntimeError('This program is designed to bridge Windows and WSL; hence, it needs to run '
                               'on Windows. Running this program on non-Windows platforms is not supported.')
            
def _verify_wsl_availability():
    # Check availability of the WSL itself
    try:
        # The top answer in https://stackoverflow.com/a/19328914 says that the output we'll get is
        # encoded in UTF-16-LE (likely because this is a Windows console/shell output), so we'll
        # specify that encoding information here.
        subprocess.run(['wsl.exe', '--version'], check=True, capture_output=True, encoding='utf-16-le')
    except CalledProcessError:
        raise RuntimeError('An error occured. Either WSL is not installed, the installed WSL doesn\'t come '
                           'with `wsl.exe` command yet, or there is an error executing `wsl.exe`. Either '
                           'way, please ensure that WSL is installed on this system (the Microsoft Store '
                           'edition is preferred).')


def verify_wsl_distro_readiness(distro_name: str = None):
    """
    Can raise a `DistroUnsupportedError` exception.
    """
    # Check systemd availability inside the default distro.
    try:
        command_list = (['wsl.exe'] +
                        (['-d', distro_name] if distro_name is not None else []) +
                        ['[', '-d', '/run/systemd/system', ']'])
        subprocess.run(command_list, check=True)
    except CalledProcessError:
        raise DistroUnsupportedError('The default WSL distribution is not booted with systemd. Enable systemd in '
                                     'the WSL configuration in order to use FancyWSL.')

def preliminary_platform_checks() -> None:
    """
    Can raise a `RuntimeError` exception.
    """
    _verify_proper_os()
    _verify_wsl_availability()
