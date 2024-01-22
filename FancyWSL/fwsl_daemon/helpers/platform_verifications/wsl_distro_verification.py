import subprocess
from subprocess import CalledProcessError
from ..create_wsl_command_runner import create_wsl_command_runner
from ..obtain_bus_address import obtain_bus_address

def is_booted_with_systemd(distro_name: str) -> bool:
    wsl_run = create_wsl_command_runner(distro_name, default_check=True)

    # Check systemd availability inside the specified distro.
    try:
        wsl_run(['[', '-d', '/run/systemd/system', ']'])
    except CalledProcessError:
        return False
    
    return True
    
def _is_dbus_available(distro_name: str) -> bool:
    """
    This function must be called AFTER verifying that systemd is
    available (with `_is_booted_with_systemd(distro_name)`).
    """
    wsl_run = create_wsl_command_runner(distro_name)

    command_result = wsl_run(['systemctl', '--user', 'status', 'dbus.service'], stdout=subprocess.DEVNULL)

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


def is_distro_ready(distro_name: str) -> bool:
    # We're assuming that this function is only called with a WSL 2 distro name as its argument.
    
    if not is_booted_with_systemd(distro_name):
        return False
    
    if not _is_dbus_available(distro_name):
        return False

    try:
        obtain_bus_address(distro_name)
    except ValueError:
        return False

    return True
