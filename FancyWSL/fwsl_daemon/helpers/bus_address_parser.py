import re

def bus_address_parser(address_string: str) -> (str, int, str | None):
    matches = re.search(r'tcp\:host=(\S+),port=(\d+)(?:,family=(ipv4|ipv6))', address_string)

    host = matches.group(1)
    port_number = matches.group(2)

    try:
        specific_family = 'IPv4' if matches.group(3) == 'ipv4' else 'IPv6'
    except IndexError:
        # family = 'IPv4 and IPv6'
        specific_family = None
    
    return (host, port_number, specific_family)
