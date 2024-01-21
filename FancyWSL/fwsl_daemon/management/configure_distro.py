from configparser import ConfigParser
import subprocess
from subprocess import CalledProcessError
from io import StringIO

from ..helpers import wsl_manager as wsl
from ..helpers.platform_verifications import (verify_wsl_distro_overall_readiness,
                                              verify_wsl_distro_systemd_support)
from ..helpers.exceptions import DistroUnsupportedError

# _EXIT_SUCCESS = 0
# _EXIT_FAILED = 1

_BACKUP_FILE_SUFFIX = '.fwsl-backup'

# def _wr(distro_name: str, *command_lists: list[str]) -> list[str]:
#     # percobaan = [c2 for c2 in c1 for c1 in commands]
#     return ['wsl.exe', '-d', distro_name, *[c2 for c1 in command_lists for c2 in c1]]

# def _wr(distro_name: str, command_strings)

# A convenience function for composing command list for running inside the WSL environment.
def _wr(distro_name: str, need_root_access: bool, wsl_command_options: list[str] | None, *command_args: str) -> list[str]:
    # return ['wsl.exe', '-d', distro_name, *[] *(wsl_command_options or []), *command_args]
    # command_list = ['wsl.exe', '-d', distro_name]
    final_command_args = ['wsl.exe', '-d', distro_name]

    if need_root_access:
        # command_list
        # final_command_args.append('a', 'b')
        # final_command_args.append('-u')
        # final_command_args.append('root')
        # final_command_args += ['-u', 'root']
        final_command_args.extend(['-u', 'root'])

    if wsl_command_options:
        # final_command_args += wsl_command_options
        final_command_args.extend(wsl_command_options)

    # final_command_args += command_args
    final_command_args.extend(command_args)

    return final_command_args

def _enable_systemd_support(distro_name: str) -> None:
    # wsl_config
    wsl_configuration = ConfigParser(delimiters=('=',))

    wsl_configuration_file_path = '/etc/wsl.conf'
    # wsl_config_file_path_quoted

    # Initialize default values first before attempting to read from the file system.
    # wsl_config_file_exists_before = False
    # wsl_config_string = ''

    try:
        wsl_configuration_string = subprocess.run(_wr(distro_name, False, None, 'cat',
                                                      wsl_configuration_file_path),
                                                  check=True, capture_output=True, encoding='utf-8').stdout
        
        # If the above command doesn't throw an error, then the below line can be reached.
        # wsl_config_file_exists_before = True

        # If the above command doesn't throw an error (indicating that the configuration file
        # already exists before), then the below lines can be reached.

        # Backup first, just in case.
        # subprocess.run(['wsl.exe', '-d'])
        print('Previous WSL configuration file exists. Creating backup before proceeding further...')
        wsl_configuration_backup_file_path = wsl_configuration_file_path + _BACKUP_FILE_SUFFIX
        subprocess.run(_wr(distro_name, True, None, 'mv', '-v', wsl_configuration_file_path,
                                         wsl_configuration_backup_file_path), check=True)
        print(f'The existing WSL configuration file has been backed up as "{wsl_configuration_backup_file_path}". '
              'Please restore from it manually if something unexpected (e.g. error) happens.')
    except CalledProcessError:
        wsl_configuration_string = ''
        # pass
    
    wsl_configuration.read_string(wsl_configuration_string)

    if ('boot' in wsl_configuration and 'systemd' in wsl_configuration['boot']
        and wsl_configuration['boot']['systemd'] == 'true'):
        print('systemd support is already enabled in the configuration. You may just need to restart this '
              'WSL distribution instance after this.')
        return
    
    wsl_configuration['boot'] = {}
    wsl_configuration['boot']['systemd'] = 'true'

    # Create a virtual file.
    # final_wsl_config_virtual_file = StringIO()

    with StringIO() as virtual_file:
        wsl_configuration.write(virtual_file, False)
        subprocess.run(_wr(distro_name, True, None, 'tee', wsl_configuration_file_path),
                       input=virtual_file.getvalue(), encoding='utf-8',
                       stdout=subprocess.DEVNULL, check=True)
        print(f'Successfully written the updated configuration file to "{wsl_configuration_file_path}".')

def _configure_dbus_listen_address(distro_name: str) -> None:
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
        subprocess.run(_wr(distro_name, False, None, '[', '!', '-f', custom_configuration_file_path, ']'))
    except CalledProcessError:
        # print(f'"{custom_configuration_file_path}" file already exists!')
        raise RuntimeError(f'"{custom_configuration_file_path}" file already exists!')
    
    subprocess.run(_wr(distro_name, True, None, 'tee', custom_configuration_file_path),
                   input=custom_configuration_content_string, encoding='utf-8', check=True)
    
    print(f'Successfully created a new D-Bus configuration file in "{custom_configuration_file_path}".')
    
    # Then, modify the main session bus configuration file to also read from the custom configuration file we
    # just wrote.

    main_session_bus_configuration_file_path = '/usr/share/dbus-1/session.conf'

    sed_script = fr's%\<listen\>unix:tmpdir=/tmp\</listen\>%\<include\>{custom_configuration_file_path}\</include\>%'
    print(sed_script)

    subprocess.run(_wr(distro_name, True, None, 'sed', '-z', f'--in-place={_BACKUP_FILE_SUFFIX}',
                       sed_script, main_session_bus_configuration_file_path), check=True)
    
    print('Successfully modified the main D-Bus session bus configuration file '
          f'in "{main_session_bus_configuration_file_path}". The original configuration file has been '
          f'backed up in "{main_session_bus_configuration_file_path}{_BACKUP_FILE_SUFFIX}".')
    
    # Finally, modify the D-Bus (session bus) service in systemd so that the <listen> addresses in this
    # configuration file don't get deprioritized anymore.

    # Get original `ExecStart` line.
    # systemd_dbus_service_file_content_string
    service_file_content_string = subprocess.run(_wr(distro_name, False, None, 'cat',
                                                                  '/usr/lib/systemd/user/dbus.service'),
                                                              check=True, capture_output=True,
                                                              encoding='utf-8').stdout
    
    # Use ConfigParser again for this because the unit file format seems to also follow the INI configuration
    # file convention.
    # systemd_dbus_service_configuration
    # service_file_parsed
    service_configuration = ConfigParser()
    # systemd_dbus_service_configuration.read_string(systemd_dbus_service_file_content_string)
    service_configuration.read_string(service_file_content_string)

    # systemd_dbus_service_execstart_line = systemd_dbus_service_configuration['Service']['ExecStart']

    # original_execstart_line = systemd_dbus_service_configuration['Service']['ExecStart']
    original_execstart_line = service_configuration['Service']['ExecStart']
    new_execstart_line = original_execstart_line.replace('--address=systemd: ', '') + ' --print-address'

    # subprocess.run(_wr(distro_name, ['--cd', '~'], ['mkdir', '-p', '']))
    # dbus_service_unit_file
    # systemd_dbus_service_file_override_directory_relative
    service_override_directory = '.config/systemd/user/dbus.service.d'
    # systemd_dbus_service_file_override_file_name
    service_override_file_name = 'fwsl-tcp-address-addition.conf'
    # systemd_dbus_service_file_override_content
    # service_override_content_string

    # We manually write the string by hand instead of using ConfigParser like above because we need to
    # explicitly specify two lines of the `ExecStart` in order for the `ExecStart` override to actually work,
    # and we don't want to configure the ConfigParser itself with e.g. some overcomplicated configurations.
    service_override_file_content_string = f"""
[Service]
ExecStart=
ExecStart={new_execstart_line}
"""
    # subprocess.run(_wr(distro_name, ['--cd', '~'], 'mkdir', '-p',
    #                    systemd_dbus_service_file_override_directory_relative), check=True)
    subprocess.run(_wr(distro_name, False, ['--cd', '~'], 'mkdir', '-v', '-p', service_override_directory),
                   check=True)
    subprocess.run(_wr(distro_name, False, ['--cd', '~'], 'tee',
                       f'{service_override_directory}/{service_override_file_name}'), check=True,
                   input=service_override_file_content_string, encoding='utf-8')
    
    print('Successfully added a new override file '
          f'in "{service_override_directory}/{service_override_file_name}" for systemd dbus.service.')
    
    # Assume that it is enough to call the termination command only one and wait for several seconds for the
    # distro to fully stop.
    subprocess.run(['wsl.exe', '--terminate', distro_name], check=True)
    print(f'The distribution "{distro_name}" has been successfully shut down.')

# This function needs to return an integer because the return value is directly passed to
# the sys.exit() function.
def configure_distro(distro_name: str) -> int:
    _exit_success = 0
    _exit_failure = 1

    # available_distros
    distros = wsl.list_distros()
    distro_names = [distro['name'] for distro in distros]

    if distro_name not in distro_names:
        print('The specified distribution does not exist in the installation of WSL on this machine.')
        return _exit_failure
    
    if [distro['version'] for distro in distros if distro['name'] == distro_name][0] != 2:
        print('The specified distribution is still a WSL 1 distribution. '
              'Please convert it manually to WSL 2 before proceeding with this process.')
        return _exit_failure
    
    try:
        verify_wsl_distro_overall_readiness(distro_name)
    except DistroUnsupportedError:
        pass
    else:
        print(f'The distribution "{distro_name}" is already configured to work with FancyWSL, so there is '
              'no need to reconfigure it again.')
        return _exit_failure
    
    # print('Notes:')
    # print('- This process may ask you for your sudo password multiple times, so be prepared to enter it!')
    print(f'IMPORTANT NOTE:\nAfter this process has completed, the specified WSL distribution ({distro_name}) will '
          'automatically be shut down (ready to be started again), so save your work (if there is any) '
          'inside the distribution before proceeding.')
    print() # Blank line
    # print('Do you want to proceed? [Y/n] ', end='')
    user_confirmation = input('Do you want to proceed? [Y/n] ')

    if len(user_confirmation) > 1 or user_confirmation.lower() not in ['y', 'n']:
        raise ValueError('Unknown value. Value can only be Y or N (in lowercase or uppercase).')
    
    # if user_confirmation.lower() not in ['y', 'n']:
    #     raise ValueError('')
    
    if user_confirmation.lower() == 'n':
        print(f'Operation cancelled. The distribution "{distro_name}" is untouched.')
        return _exit_success
    
    try:
        verify_wsl_distro_systemd_support(distro_name)
    except DistroUnsupportedError:
        _enable_systemd_support(distro_name)

    try:
        _configure_dbus_listen_address(distro_name)
    except RuntimeError as e:
        print(e.args[0])
        return _exit_failure

    print(f'The distribution "{distro_name}" has been successfully configured to work with FancyWSL. Enjoy!')
    return _exit_success
