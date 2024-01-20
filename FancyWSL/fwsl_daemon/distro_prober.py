from logging import getLogger
from asyncio import sleep, CancelledError, create_task, Task
from typing import Callable

# from .helpers.wsl_manager import wsl_list_distros
from .helpers import wsl_manager as wsl
from .distro_connection_instance import DistroConnectionInstance
from .helpers.exceptions import DistroUnsupportedError

_logger = getLogger('distro_prober')

async def distro_prober(distro_count_change_callback: Callable[[int], None]):
    """
    Note: This function is meant to be run as a separate asyncio task (because it is blocking).
    """
    # ConnectionItemType = tuple[DistroConnectionInstance, Task]
    # _connections: set[ConnectionItemType] = set()

    # def get_connections():
    #     return _connections

    # def add_to_connections(element: ConnectionItemType) -> None:
    #     _connections.add(element)
    #     distro_count_change_callback(len(_connections))

    # def remove_from_connections(element):
    #     _connections.remove(element)
    #     distro_count_change_callback(len(_connections))

        # previous_distro_names = None

    # _tasks: set[Task] = set()

    # Using a set is kind of useless here (and just complicates things further)
    # since each Task is (inherently?) always unique (so we can't even remove the elements
    # inside the set).
    _tasks: list[Task] = []

    def get_tasks():
        return _tasks
    
    def add_to_tasks(new_task: Task) -> None:
        _tasks.append(new_task)
        distro_count_change_callback(len(_tasks))

    def remove_from_tasks(reference_task: Task) -> None:
        # _tasks.remove(task)
        for task in _tasks:
            if task.get_name() == reference_task.get_name():
                _tasks.remove(task)
                break

        distro_count_change_callback(len(_tasks))

    previous_distro_names: set[str] = set()

    try:
        while True:
            # current_distro_names = {distro['name'] for distro in wsl.list_distros() if distro['version'] == 2}
            new_distro_names = {distro['name'] for distro in wsl.list_distros() if distro['version'] == 2}

            # It is considered impossible for the current list to have less members than the previous list
            # because the way the entire logic is designed (completed instances are automatically removed
            # immediately via the completion callback), but still check it anyway just in case.

            # if len(current_distro_names) < len(previous_distro_names):
            # if len(distro_names) < len(get_connections()):
            if len(new_distro_names) < len(previous_distro_names):
                # raise RuntimeError('Current distribution list somehow has less members than the previous'
                #                    'distribution list.')
                raise RuntimeError('Newly-obtained list of distributions somehow has less members than '
                                   'the currently-connected distributions.')
            
            # if len(current_distro_names) > len(previous_distro_names):
            # if len(distro_names) > len(get_connections()):
            if len(new_distro_names) > len(previous_distro_names):
                # connected_distro_names = [item.distro_name for item in get_connections()]
                # new_distro_names = [name for name in distro_names if name not in connected_distro_names]

                unconnected_distro_names = [name
                                            for name in new_distro_names
                                            if name not in previous_distro_names]

                # for distro_name in new_distro_names:
                for distro_name in unconnected_distro_names:
                    # dci = DistroConnectionInstance(distro_name, remove_from_connections)
                    try:
                        dci = DistroConnectionInstance(distro_name)
                        await dci.connect()
                    except DistroUnsupportedError:
                        continue

                    task = create_task(dci.enter_loop())
                    task.add_done_callback(remove_from_tasks)
                    # add_to_connections()
                    add_to_tasks(task)

            await sleep(5)

            # previous_distro_list = current_distro_list
            previous_distro_names = new_distro_names
    # except CancelledError:
    finally:
        # Disconnect the still-existing connections.
        # for item in get_connections():
        #     item.disconnect_manually()
        # try:
        for task in get_tasks():
            try:
                task.cancel()
            # except CancelledError:
            #     raise
            # except CancelledError as e:
            except CancelledError:
                # _logger.info('Got a CancelledError exception with arguments ""')
                _logger.info('Got a CancelledError exception, indicating that the task has been '
                             'successfully cancelled.')
        
        _tasks.clear()
