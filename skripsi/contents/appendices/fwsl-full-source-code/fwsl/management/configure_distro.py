from configparser import ConfigParser
import subprocess
from subprocess import CalledProcessError
from io import StringIO
from ..helpers.create_wsl_command_runner import create_wsl_command_runner
from ..helpers import wsl_manager as wsl
from ..helpers.platform_verifications import wsl_distro_verification

_BACKUP_FILE_SUFFIX = '.fwsl-backup'

def _enable_systemd_support(distro_name: str) -> None:
    wsl_run = create_wsl_command_runner(distro_name, default_check=True)

    wsl_configuration = ConfigParser(delimiters=('=',))

    wsl_configuration_file_path = '/etc/wsl.conf'

    try:
        wsl_configuration_string = wsl_run(['cat', wsl_configuration_file_path],
                                           capture_output=True, encoding='utf-8').stdout
                
        # If the above command doesn't throw an error (indicating that the configuration file
        # already exists before), then the below lines can be reached.

        # Backup first, just in case.
        print('Previous WSL configuration file exists. Creating backup before proceeding further...')
        wsl_configuration_backup_file_path = wsl_configuration_file_path + _BACKUP_FILE_SUFFIX
        wsl_run(['mv', '-v', wsl_configuration_file_path, wsl_configuration_backup_file_path],
                run_as_root=True)
        print(f'The existing WSL configuration file has been backed up as "{wsl_configuration_backup_file_path}". '
              'Please restore from it manually if something unexpected (e.g. error) happens.')
    except CalledProcessError:
        wsl_configuration_string = ''
    
    wsl_configuration.read_string(wsl_configuration_string)

    if ('boot' in wsl_configuration and 'systemd' in wsl_configuration['boot']
        and wsl_configuration['boot']['systemd'] == 'true'):
        print('systemd support is already enabled in the configuration. You may just need to restart this '
              'WSL distribution instance after this.')
        return
    
    wsl_configuration['boot'] = {}
    wsl_configuration['boot']['systemd'] = 'true'

    # Use a virtual file for holding the eventual string content.
    with StringIO() as virtual_file:
        wsl_configuration.write(virtual_file, False)
        wsl_run(['tee', wsl_configuration_file_path], run_as_root=True, input=virtual_file.getvalue(),
                encoding='utf-8', stdout=subprocess.DEVNULL)
        print(f'Successfully written the updated configuration file to "{wsl_configuration_file_path}".')

def _configure_dbus_listen_address(distro_name: str) -> None:
    wsl_run = create_wsl_command_runner(distro_name, default_check=True)

    # Write the custom configuration file first.

    # The only flag (indication) that the WSL distro has been modified to work with FancyWSL is this custom
    # configuration file.
    custom_configuration_file_path = '/etc/dbus-1/session-local-fwsl.conf'

    custom_configuration_content_string = """
<!DOCTYPE busconfig PUBLIC "-//freedesktop//DTD D-Bus Bus Configuration 1.0//EN" "http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">
<busconfig>
    <listen>systemd:</listen>
    <listen>tcp:host=localhost,port=0</listen>
    <auth>ANONYMOUS</auth>
    <allow_anonymous />
</busconfig>
"""

    try:
        wsl_run(['[', '!', '-f', custom_configuration_file_path, ']'])
    except CalledProcessError:
        raise RuntimeError(f'"{custom_configuration_file_path}" file already exists!')
    
    wsl_run(['tee', custom_configuration_file_path], run_as_root=True,
            input=custom_configuration_content_string, encoding='utf-8', stdout=subprocess.DEVNULL)
    
    print(f'Successfully created a new D-Bus configuration file in "{custom_configuration_file_path}".')
    
    # Then, modify the main session bus configuration file to also read from the custom configuration file we
    # just wrote.

    main_session_bus_configuration_file_path = '/usr/share/dbus-1/session.conf'

    sed_script = fr's%\<listen\>unix:tmpdir=/tmp\</listen\>%\<include\>{custom_configuration_file_path}\</include\>%'
    wsl_run(['sed', '-z', f'--in-place={_BACKUP_FILE_SUFFIX}', sed_script,
             main_session_bus_configuration_file_path], run_as_root=True)
    
    print('Successfully modified the main D-Bus session bus configuration file '
          f'in "{main_session_bus_configuration_file_path}". The original configuration file has been '
          f'backed up in "{main_session_bus_configuration_file_path}{_BACKUP_FILE_SUFFIX}".')
    
    # Finally, modify the D-Bus (session bus) service in systemd so that the <listen> addresses in this
    # configuration file don't get deprioritized anymore.

    # Get original `ExecStart` line.
    service_file_content_string = wsl_run(['cat', '/usr/lib/systemd/user/dbus.service'],
                                          capture_output=True, encoding='utf-8').stdout
    
    # Use ConfigParser again for this because the unit file format seems to also follow the INI configuration
    # file convention.
    service_configuration = ConfigParser()
    service_configuration.read_string(service_file_content_string)

    original_execstart_line = service_configuration['Service']['ExecStart']
    new_execstart_line = original_execstart_line.replace('--address=systemd: ', '') + ' --print-address'

    service_override_directory_relative = '.config/systemd/user/dbus.service.d'
    service_override_file_name = 'fwsl-tcp-address-addition.conf'

    # We manually write the string by hand instead of using ConfigParser like above because we need to
    # explicitly specify two lines of the `ExecStart` in order for the `ExecStart` override to actually work,
    # and we don't want to configure the ConfigParser itself with e.g. some overcomplicated configurations.
    service_override_file_content_string = f"""
[Service]
ExecStart=
ExecStart={new_execstart_line}
"""
    wsl_run(['mkdir', '-v', '-p', service_override_directory_relative], cd='~')
    wsl_run(['tee', f'{service_override_directory_relative}/{service_override_file_name}'], cd='~',
            input=service_override_file_content_string, encoding='utf-8', stdout=subprocess.DEVNULL)
    
    print('Successfully added a new override file '
          f'in "~/{service_override_directory_relative}/{service_override_file_name}" for systemd dbus.service.')
    
    # Assume that it is enough to call the termination command only one and wait for several seconds for the
    # distro to fully stop.
    subprocess.run(['wsl.exe', '--terminate', distro_name], check=True)
    print(f'{distro_name} has been successfully shut down.')

# This function needs to return an integer because the return value is directly passed to
# the sys.exit() function.
def configure_distro(distro_name: str) -> int:
    _exit_success = 0
    _exit_failure = 1

    distros = wsl.list_distros()
    distro_names = [distro['name'] for distro in distros]

    if distro_name not in distro_names:
        print('The specified distribution does not exist in the installation of WSL on this machine.')
        return _exit_failure
    
    if [distro['version'] for distro in distros if distro['name'] == distro_name][0] != 2:
        print('The specified distribution is still a WSL 1 distribution. '
              'Please convert it manually to WSL 2 before proceeding with this process.')
        return _exit_failure
    
    if wsl_distro_verification.is_distro_ready(distro_name):
        print(f'{distro_name} is already configured to work with FancyWSL, so there is '
              'no need to reconfigure it again.')
        return _exit_failure
    
    print() # Blank line

    print(f'IMPORTANT NOTE:\nAfter this process has completed, the specified WSL distribution ({distro_name}) will '
          'automatically be shut down (ready to be started again), so save your work (if there is any) '
          'inside the distribution before proceeding.')
    
    print() # Blank line

    user_confirmation = input('Do you want to proceed? [Y/n] ')

    print() # Blank line

    if len(user_confirmation) > 1 or user_confirmation.lower() not in ['y', 'n']:
        raise ValueError('Unknown value. Value can only be Y or N (in lowercase or uppercase).')
        
    if user_confirmation.lower() == 'n':
        print(f'Operation cancelled. The distribution "{distro_name}" is untouched.')
        return _exit_success
    
    if not wsl_distro_verification.is_booted_with_systemd(distro_name):
        _enable_systemd_support(distro_name)

    try:
        _configure_dbus_listen_address(distro_name)
    except RuntimeError as e:
        print(e.args[0])
        return _exit_failure

    print(f'{distro_name} has been successfully configured to work with FancyWSL. Enjoy!')
    return _exit_success
