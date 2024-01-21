import logging
from argparse import ArgumentParser
import asyncio
import sys

from .helpers.platform_verifications import preliminary_platform_checks
from .helpers.spawn_win32_alert_window import spawn_win32_alert_window
from .fwsld import FancyWSLDaemon
# from .management.list_distros import list_distributions
from .management.list_distros import print_distros
from .management.configure_distro import configure_distro

def setup_and_get_arguments():
    parser = ArgumentParser('FancyWSL Daemon')

    # root_group = parser.add_mutually_exclusive_group

    # primary_subparser = root_parser.add_subparsers

    # parser.add_argument('-l', '--list-wsl-distributions')

    parser.add_argument('-l', '--list-distributions',
                        help=('List WSL distributions and whether they are available '
                              'to work with FancyWSL or not, and then exit immediately.'),
                        action='store_true')
    
    parser.add_argument('-c', '--configure-distribution', type=str,
                        help='Configure the specified distribution to work with FancyWSL.')

    # parser.add_argument('-d', '--wsl-distribution',
    #                     help='Specify the WSL distribution to be used by FancyWSL.', type=str)

    parser.add_argument('-v', '--verbose', help='Print more logs verbosely.', action='store_true')
    
    return parser.parse_args()

class _AlertWindowLogHandler(logging.Handler):
    def __init__(self, level = logging.ERROR) -> None:
        super().__init__(level)

    def emit(self, record) -> None:
        # name, msg = record

        partial_title = ['An error occured']
        if record.name != 'root':
            partial_title.append(f'in {record.name}')

        # This call is actually blocking because it waits for the user response for the
        # displayed alert window.
        spawn_win32_alert_window(' '.join(partial_title), record.getMessage())
    
def main():
    # Do platform checks first and foremost.
    try:
        preliminary_platform_checks()
    except RuntimeError as e:
        root_logger.error(e.args[0])
        # spawn_win32_alert_window('An error occured while launching FancyWSL daemon', e.args[0])
        # return
        raise

    args = setup_and_get_arguments()

    # if args.list_wsl_distributions

    if args.list_distributions:
        # print_distributions()
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
    fwsld_instance = FancyWSLDaemon()
    asyncio.run(fwsld_instance.start())

if __name__ == '__main__':
    main()
