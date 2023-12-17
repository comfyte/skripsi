import platform
import sys
import subprocess
from subprocess import CalledProcessError

def _verify_proper_os() -> bool:
    if platform.system() != 'Windows':
        if platform.system() == 'Linux' and (platform.uname().release.endswith('-Microsoft') or
                                             platform.uname().release.endswith('microsoft-standard-WSL')):
            print('This program needs to be launched in a Windows environment, not inside WSL. '
                  'Exiting...', file=sys.stderr)
        else:
            print('This program is designed to bridge Windows and WSL; hence, it needs to run on Windows. '
                  'Running this program on non-Windows platforms is not supported. Exiting...',
                  file=sys.stderr)
            
        return False
    
    return True

def _verify_wsl_availability() -> bool:
    # Check availability of the WSL itself
    try:
        # The top answer in https://stackoverflow.com/a/19328914 says that the output we'll get is
        # encoded in UTF-16-LE (likely because this is a Windows console/shell output), so we'll
        # specify that encoding information here.
        wsl_version = subprocess.run(['wsl.exe', '--version'], check=True, capture_output=True,
                                     encoding='utf-16-le')
    except CalledProcessError:
        print('An error occured. Either WSL is not installed, the installed WSL doesn\'t come '
              'with `wsl.exe` command yet, or there is an error executing `wsl.exe`. '
              'Either way, please ensure that WSL is installed on this system (the Microsoft '
              'Store edition is preferred). Exiting...', file=sys.stderr)
        return False

    print('WSL installation detected.')
    print(wsl_version.stdout)

    # Ensure that there is/are installed distro(s) in WSL and that the default distro has version 2 (WSL2).
    # FIXME: This is just comparing strings and is likely very fragile
    # (e.g. not accounting different locale, string change between WSL updates).
    wsl_list_of_installed_distros = subprocess.run(['wsl.exe', '--list', '--verbose'], capture_output=True,
                                                   encoding='utf-16-le')
    
    wsl_list_of_installed_distros_parsed = wsl_list_of_installed_distros.stdout.split()

    # Asterisk indicates that the distro is the default distro.
    # This method is likely very fragile.
    asterisk_index = wsl_list_of_installed_distros_parsed.index('*')
    wsl_default_distro_name = wsl_list_of_installed_distros_parsed[asterisk_index + 1]
    wsl_default_distro_version = int(wsl_list_of_installed_distros_parsed[asterisk_index + 3])

    print(f'FancyWSL is currently limited to working with the default WSL distribution, so this program '
          'will query the default distribution in this system.')

    print(f'Detected default distribution: {wsl_default_distro_name} (WSL{wsl_default_distro_version}).')

    if wsl_default_distro_version != 2:
         print(f'This program only supports WSL2 default distribution, but the default distribution '
               '({wsl_default_distro_name}) has version 1 (WSL1). As this program currently only works '
               'with the default distribution, consider changing the version of the default distribution '
               'to version 2 (WSL2) or changing the default distribution to a WSL2 distribution.',
               file=sys.stderr)
         return False
    
    print(f'FancyWSL will use the default distribution ({wsl_default_distro_name}).')


    # Check systemd availability inside the default distro.
    try:
        subprocess.run(['wsl.exe', '[', '-d', '/run/systemd/system', ']'], check=True)
    except CalledProcessError:
        print('The default WSL distribution is not booted with systemd. Enable systemd in the WSL '
              'configuration in order to use FancyWSL. Exiting...', file=sys.stderr)
        return False
    
    return True

# def check_proper_environment():
def verify_platform() -> None:
    if not (_verify_proper_os() and _verify_wsl_availability()):
        print('ne')
        raise RuntimeError()
