import subprocess

def create_wsl_command_runner(distro_name: str, *, default_check: bool = False):
    def final_function(_args: list[str],
                       run_as_root: bool = False,
                       cd: str = None,
                       check: bool = default_check,
                       *subprocess_run_args,
                       **subprocess_run_kwargs) -> subprocess.CompletedProcess:
        command_args: list[str] = ['wsl.exe', '-d', distro_name]

        if run_as_root:
            command_args.extend(['-u', 'root'])
        
        if cd:
            command_args.extend(['--cd', cd])

        command_args.extend(_args)

        return subprocess.run(command_args, check=check, *subprocess_run_args, **subprocess_run_kwargs)
    
    return final_function
