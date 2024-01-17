import subprocess
import re
import logging

# Get logger for current module
_logger = logging.getLogger(__name__)

def obtain_bus_address(distro_name: str):
    command_list = (['wsl.exe'] +
                    (['-d', distro_name] if distro_name is not None else []) +
                    ['journalctl', '--user', '-b', '-u', 'dbus.service'])
    command_result = subprocess.run(command_list, check=True, capture_output=True, encoding='utf-8')

    lines_reversed = reversed(command_result.stdout.splitlines())

    compiled_regex = re.compile(r'tcp\:host=\S+,port=\d+(?:,family=(?:ipv4|ipv6))?')

    for line in lines_reversed:
        result = compiled_regex.search(line)
        if result is not None:
            bus_address = result.group(0)
            _logger.info('Successfully obtained bus address for the '
                         f'selected distro "{distro_name}": "{bus_address}".')
            return bus_address
            
    # Else
    raise RuntimeError('TCP address not found')
