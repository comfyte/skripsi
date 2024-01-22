import subprocess
import re
import logging
from typing import TypedDict, NotRequired, Literal

# Get logger for current module
_logger = logging.getLogger(__name__)

class BusAddressResult(TypedDict):
    full_address: str
    host: str
    port: int
    # family: NotRequired[Literal['ipv4', 'ipv6']]
    family: Literal['ipv4', 'ipv6'] | None

def obtain_bus_address(distro_name: str) -> BusAddressResult:
    command_list = (['wsl.exe'] +
                    (['-d', distro_name] if distro_name is not None else []) +
                    ['journalctl', '--user', '-b', '-u', 'dbus.service'])
    command_result = subprocess.run(command_list, check=True, capture_output=True, encoding='utf-8')

    lines_reversed = reversed(command_result.stdout.splitlines())

    compiled_regex = re.compile(r'tcp\:host=(\S+),port=(\d+)(?:,family=(ipv4|ipv6))?')

    for line in lines_reversed:
        result = compiled_regex.search(line)
        if result is not None:
            # full_address = result.group(0)
            # host = result.group(1)
            full_address, host, port, family = result.group(0, 1, 2, 3)
            _logger.info(f'Port number for "{distro_name}" is {port}.')
            return {'full_address': full_address,
                    'host': host,
                    'port': int(port),
                    'family': family}
            
    # Else
    raise ValueError('TCP address not found')
