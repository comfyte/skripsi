from ..helpers import wsl_manager as wsl
# from ..helpers.platform_verifications import verify_wsl_distro_overall_readiness
from ..helpers.platform_verifications import wsl_distro_verification
# from ..helpers.obtain_bus_address import obtain_bus_address
from ..helpers.exceptions import DistroUnsupportedError

def _print_name(distro_item: wsl.DistroItem):
    final_name = distro_item['name']
    if distro_item['is_default']:
        final_name += ' (Default)'
    return final_name

# def print_distributions():
def print_distros():
    print('Getting information... (This might take a while)')
    
    # return 'lorem ipsum'
    distros = wsl.list_distros()

    usable_distros: list[wsl.DistroItem] = []
    stopped_distros: list[wsl.DistroItem] = []
    wsl1_distros: list[wsl.DistroItem] = []
    unconfigured_distros: list[wsl.DistroItem] = []

    for distro in distros:
        # if distro['version'] == 2 and distro['state']
        if distro['version'] == 1:
            wsl1_distros.append(distro)
        elif distro['state'] == 'Stopped':
            stopped_distros.append(distro)
        elif not wsl_distro_verification.is_distro_ready(distro['name']):
            unconfigured_distros.append(distro)
        else:
            usable_distros.append(distro)

    print('Done getting information.')

    print() # Blank line

    print('Below list determines whether a particular distribution can be used with FancyWSL or not.')

    print() # Blank line

    print('Available distributions:')
    if len(usable_distros) > 0:
        for distro in usable_distros:
            # print(f'- {distro["name"]}{" (Default)" if distro["is_default"] else ""}')
            print(f'- {_print_name(distro)}')
    else:
        print('(None)')

    print() # Blank line

    # print('Unsupported distributions:')
    print('Unavailable distributions:')
    if len(unconfigured_distros) > 0 or len(wsl1_distros) > 0:
        for distro in unconfigured_distros:
            print(f'- {_print_name(distro)} (need configuration)')
    # else:
    #     print('(None)')

    # for distro in stopped_distros:
    #     print(f'- {distro["name"]} (not running)')
        
    # if len(wsl1_distros) > 0:
        for distro in wsl1_distros:
            print(f'- {_print_name(distro)} (not a WSL 2 distribution)')
    else:
        print('(None)')

    print() # Blank line

    print('Stopped distributions (run them to determine their compatibility with FancyWSL):')
    if len(stopped_distros) > 0:
        for distro in stopped_distros:
            print(f'- {_print_name(distro)}')
    else:
        print('(None)')
    
    # print()
