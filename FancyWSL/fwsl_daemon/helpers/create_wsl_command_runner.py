import subprocess
# from typing import Callable, Any
# from typing import Any

# def _create_wsl_runner_function(distro_name: str):
# def create_runner_function
def create_wsl_command_runner(distro_name: str, *, default_check: bool = False):
    def final_function(_args: list[str],
                       run_as_root: bool = False,
                       cd: str = None,
                       check: bool = default_check,
                       *subprocess_run_args,
                       **subprocess_run_kwargs) -> subprocess.CompletedProcess:
        # args: list[str] = ['wsl.exe', '-d', distro_name]
        command_args: list[str] = ['wsl.exe', '-d', distro_name]

        if run_as_root:
            command_args.extend(['-u', 'root'])
        
        if cd:
            command_args.extend(['--cd', cd])

        command_args.extend(_args)

        return subprocess.run(command_args, check=check, *subprocess_run_args, **subprocess_run_kwargs)
    
    return final_function
