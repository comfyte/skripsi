from logging import getLogger
from asyncio import sleep, CancelledError, create_task, Task
from typing import Callable
from .helpers import wsl_manager as wsl
from .distro_connection_instance import DistroConnectionInstance
from .helpers.exceptions import DistroUnsupportedError

_logger = getLogger('distro_prober')

async def distro_prober(distro_count_change_callback: Callable[[int], None]):
    _current_tasks: list[Task] = []

    def get_current_tasks():
        return _current_tasks
    
    def add_to_current_tasks(new_task: Task) -> None:
        # Just in case
        for task in _current_tasks:
            if task.get_name() == new_task.get_name():
                raise NameError('There are somehow two (or more) tasks with the same name')
            
        _current_tasks.append(new_task)
        distro_count_change_callback(len(_current_tasks))

    def remove_from_current_tasks(reference_task: Task) -> None:
        reference_task_name = reference_task.get_name()
        _logger.info(f'Task for "{reference_task_name}" is finished.')
        for task in _current_tasks:
            # _logger.info(_tasks)
            if task.get_name() == reference_task_name:
                _current_tasks.remove(task)
                break

        distro_count_change_callback(len(_current_tasks))

    try:
        while True:
            detected_distro_names = [distro['name']
                                     for distro in wsl.list_distros()
                                     if distro['version'] == 2 and distro['state'] == 'Running']

            # This is considered a very-edge case (a nearly impossible case) because each connection task is
            # automatically removed from the list once it is disconnected.
            if len(detected_distro_names) < len(get_current_tasks()):
                raise RuntimeError('Newly-obtained list of distributions somehow has less members than '
                                   'the currently-connected distributions.')
            
            if len(detected_distro_names) > len(get_current_tasks()):
                current_distro_names = [task.get_name() for task in get_current_tasks()]

                unconnected_distro_names = [name
                                            for name in detected_distro_names
                                            if name not in current_distro_names]

                for distro_name in unconnected_distro_names:
                    try:
                        dci = DistroConnectionInstance(distro_name)
                        _logger.info(f'Detected "{distro_name}".')
                        await dci.connect()
                    except DistroUnsupportedError:
                        continue

                    # Use the distro name for identifying the task.
                    task = create_task(dci.enter_loop(), name=distro_name)

                    task.add_done_callback(remove_from_current_tasks)

                    add_to_current_tasks(task)

            # Set time interval long enough to (hopefully) prevent any race condition from happening,
            # but also quick enough that the distros can be refreshed quite-swiftly. I think 30 seconds is
            # a decent compromise here.
            await sleep(30)
    finally:
        # Disconnect the still-existing connections.
        for task in get_current_tasks():
            try:
                task.cancel()
            except CancelledError:
                _logger.info('Got a CancelledError exception, indicating that the task has been '
                             'successfully cancelled.')
        
        _current_tasks.clear()
