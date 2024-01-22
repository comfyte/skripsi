import logging
from argparse import ArgumentParser
import asyncio
import sys
from .helpers.platform_verifications import host_os_verification
from .helpers.spawn_win32_alert_window import spawn_win32_alert_window
from . import fwsld
from .management.list_distros import print_distros
from .management.configure_distro import configure_distro

def setup_and_get_arguments():
    parser = ArgumentParser('FancyWSL Daemon')

    parser.add_argument('-l', '--list-distributions',
                        help=('List WSL distributions and whether they are available '
                              'to work with FancyWSL or not, and then exit immediately.'),
                        action='store_true')
    
    parser.add_argument('-c', '--configure-distribution', type=str,
                        help='Configure the specified distribution to work with FancyWSL.')

    parser.add_argument('-v', '--verbose', help='Print more logs verbosely.', action='store_true')
    
    return parser.parse_args()

class _AlertWindowLogHandler(logging.Handler):
    def __init__(self, level = logging.ERROR) -> None:
        super().__init__(level)

    def emit(self, record) -> None:
        final_title = ['An error occured']
        if record.name != 'root':
            final_title.append(f'in {record.name}')

        # This call is actually blocking because it waits for the user response for the
        # displayed alert window.
        spawn_win32_alert_window(' '.join(final_title), record.getMessage())
    
def main() -> None:
    # Do platform checks first and foremost.
    try:
        host_os_verification.check_all()
    except RuntimeError as e:
        root_logger.error(e.args[0])
        raise

    args = setup_and_get_arguments()

    if args.list_distributions:
        print_distros()
        return
    
    if args.configure_distribution:
        sys.exit(configure_distro(args.configure_distribution))

    logging.basicConfig(format='FWSL LOG | %(asctime)s | (%(name)s) %(levelname)s: %(message)s',
                        level=logging.INFO if args.verbose else logging.WARNING)
    root_logger = logging.getLogger()

    # Add additional handler for displaying logs of level "ERROR" as GUI alert window.
    root_logger.addHandler(_AlertWindowLogHandler())

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Run main loop
    asyncio.run(fwsld.start())

if __name__ == '__main__':
    main()
