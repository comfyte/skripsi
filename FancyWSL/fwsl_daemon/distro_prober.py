from logging import getLogger
from asyncio import sleep, CancelledError, create_task, Task
from typing import Callable

from .helpers import wsl_manager as wsl
from .distro_connection_instance import DistroConnectionInstance
from .helpers.exceptions import DistroUnsupportedError

_logger = getLogger('distro_prober')

async def distro_prober(distro_count_change_callback: Callable[[int], None]):
    """
    Note: This function is meant to be run as a separate asyncio task (because it is blocking).
    """
    _tasks: list[Task] = []

    def get_tasks():
        return _tasks
    
    def add_to_tasks(new_task: Task) -> None:
        _tasks.append(new_task)
        distro_count_change_callback(len(_tasks))

    def remove_from_tasks(reference_task: Task) -> None:
        for task in _tasks:
            if task.get_name() == reference_task.get_name():
                _tasks.remove(task)
                break

        distro_count_change_callback(len(_tasks))

    previous_distro_names: set[str] = set()

    try:
        while True:
            new_distro_names = [distro['name']
                                for distro in wsl.list_distros()
                                if distro['version'] == 2 and distro['state'] == 'Running']

            # This is considered a very-edge case (a nearly impossible case) because each connection task is
            # automatically removed from the list once it is disconnected.
            if len(new_distro_names) < len(previous_distro_names):
                raise RuntimeError('Newly-obtained list of distributions somehow has less members than '
                                   'the currently-connected distributions.')
            
            if len(new_distro_names) > len(previous_distro_names):
                unconnected_distro_names = [name
                                            for name in new_distro_names
                                            if name not in previous_distro_names]

                for distro_name in unconnected_distro_names:
                    try:
                        dci = DistroConnectionInstance(distro_name)
                        await dci.connect()
                    except DistroUnsupportedError:
                        continue

                    task = create_task(dci.enter_loop())
                    task.add_done_callback(remove_from_tasks)
                    add_to_tasks(task)

            await sleep(5)

            previous_distro_names = new_distro_names
    finally:
        # Disconnect the still-existing connections.
        for task in get_tasks():
            try:
                task.cancel()
            except CancelledError:
                _logger.info('Got a CancelledError exception, indicating that the task has been '
                             'successfully cancelled.')
        
        _tasks.clear()
