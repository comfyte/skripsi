import subprocess
import re

def obtain_bus_address(distro_name: str) -> str:
    # bash_command_string_quoted = ('"journalctl --user -b -u dbus.service | '
    #                               'grep \'dbus-daemon\' | '
    #                               'tail -n 1 | '
    #                               'grep -P -o \'tcp\\:host=\\S+,port=\\d+(?:,family=(?:ipv4|ipv6))?\'"')
    
    # command_result = subprocess.run(['wsl.exe', '-d', distro_name, 'bash', '-c', bash_command_string_quoted],
    #                                 check=True, capture_output=True, encoding='utf-8')

    command_result = subprocess.run(['wsl.exe', '-d', distro_name,
                                     'journalctl', '--user', '-b', '-u', 'dbus.service'],
                                    check=True,
                                    capture_output=True,
                                    encoding='utf-8')
    
    lines_reversed = reversed(command_result.stdout.splitlines())

    compiled_regex = re.compile(r'tcp\:host=\S+,port=\d+(?:,family=(?:ipv4|ipv6))?')

    for line in lines_reversed:
        result = compiled_regex.search(line)
        if result is not None:
            return result.group(0)
    
    # return command_result.stdout
