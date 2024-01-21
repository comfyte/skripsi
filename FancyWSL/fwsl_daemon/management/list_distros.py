from ..helpers import wsl_manager as wsl
from ..helpers.platform_verifications import verify_wsl_distro_overall_readiness
# from ..helpers.obtain_bus_address import obtain_bus_address
from ..helpers.exceptions import DistroUnsupportedError

# def print_distributions():
def print_distros():
    # return 'lorem ipsum'
    distros = wsl.list_distros()

    usable_distros: list[wsl.DistroItem] = []
    # unusable_distros = []
    stopped_distros: list[wsl.DistroItem] = []
    wsl1_distros: list[wsl.DistroItem] = []
    unconfigured_distros: list[wsl.DistroItem] = []

    for distro in distros:
        # if distro['version'] == 2 and distro['state']
        if distro['version'] == 1:
            wsl1_distros.append(distro)
        elif distro['state'] == 'Stopped':
            stopped_distros.append(distro)
        else:
            try:
                verify_wsl_distro_overall_readiness(distro['name'])
                # obtain_bus_address(distro['name'])
            except DistroUnsupportedError:
                unconfigured_distros.append(distro)
            else:
                usable_distros.append(distro)

    print('Below list determines whether a particular distribution can be used with FancyWSL or not.')

    print() # Blank line

    print('Available distributions:')
    for distro in usable_distros:
        print(f'- {distro["name"]}{" (Default)" if distro["is_default"] else ""}')

    print() # Blank line

    # print('Unsupported distributions:')
    print('Unavailable distributions:')
    for distro in unconfigured_distros:
        print(f'- {distro["name"]} (not configured to work with FancyWSL yet)')
    for distro in stopped_distros:
        print(f'- {distro["name"]} (not running)')
    for distro in wsl1_distros:
        print(f'- {distro["name"]} (not a WSL 2 distribution)')
    
    # print()
