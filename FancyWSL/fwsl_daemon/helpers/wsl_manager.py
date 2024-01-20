import subprocess

def list_distros() -> dict:
    command_result = subprocess.run(['wsl.exe', '--list', '--verbose'], check=True, capture_output=True,
                                    encoding='utf-16-le')
    
    lines = command_result.stdout.splitlines()

    final_result = []

    for index, line in enumerate(lines):
        if index == 0:
            continue

        parsed_items = line.split()

        is_default_distro = False

        if parsed_items[0] == '*':
            is_default_distro = True
            parsed_items.pop(0)

        [name, state, version] = parsed_items

        final_result.append({'name': name,
                             'state': state,
                             'version': int(version),
                             'is_default': is_default_distro})
        
    return final_result
