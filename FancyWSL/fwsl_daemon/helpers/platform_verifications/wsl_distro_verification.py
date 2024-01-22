import subprocess
from subprocess import CalledProcessError

from ..create_wsl_command_runner import create_wsl_command_runner
from ..obtain_bus_address import obtain_bus_address
from ..exceptions import DistroUnsupportedError

# def _wsl_distro_systemd(distro_name: str = None) -> None:
def is_booted_with_systemd(distro_name: str) -> bool:
    wsl_run = create_wsl_command_runner(distro_name, default_check=True)

    # Check systemd availability inside the default distro.
    try:
        # wsl_run(['wsl.exe'] + (['-d', distro_name] if distro_name is not None else [])
        #         + ['[', '-d', '/run/systemd/system', ']'])
        wsl_run(['[', '-d', '/run/systemd/system', ']'])
        # subprocess.run(command_list, check=True)
    except CalledProcessError:
        # raise DistroUnsupportedError('The default WSL distribution is not booted with systemd. '
        #                              'Enable systemd in the WSL configuration in order to use FancyWSL.')
        # return (False, 'Not booted with systemd')
        return False
    
    return True
    
def _is_dbus_available(distro_name: str) -> bool:
    """
    This function must be called AFTER verifying that systemd is
    available (with `_is_booted_with_systemd(distro_name)`).
    """
    wsl_run = create_wsl_command_runner(distro_name)

    # wsl_run(['wsl.exe', '-d', distro_name, 'systemctl', '--user', 'is-active', 'dbus.service',
    #          '--quiet'])
    command_result = wsl_run(['systemctl', '--user', 'status', 'dbus.service'], stdout=subprocess.DEVNULL)

    # if command_result.returncode == 0:
    #     return True
    if command_result.returncode == 3:
        try:
            wsl_run(['systemctl', '--user', 'start', 'dbus.service'], check=True, stdout=subprocess.DEVNULL)
        except CalledProcessError:
            return False
        
        return True
    
    # We're actually the most interested in the return code 4 here, but catch all the
    # other return codes anyway.
    if command_result.returncode != 0:
        return False
    
    return True

        # The line below will only get executed if systemctl successfully starts the D-Bus service.
        # return True
    # except CalledProcessError:
    #     # raise DistroUnsupportedError('D-Bus is either not running or not available')
    #     # return (False, 'D-Bus unavailable')
    #     return False
    
    # return (True,)

def is_distro_ready(distro_name: str) -> bool:
    # TODO: Add check of distro's WSL version (WSL 1 or WSL 2) here.

    if not is_booted_with_systemd(distro_name):
        return False
    
    if not _is_dbus_available(distro_name):
        return False

    # TODO: Add check of whether the specified distro has been configured to work with FancyWSL or not.
    try:
        obtain_bus_address(distro_name)
    except ValueError:
        # raise DistroUnsupportedError
        return False

    return True
