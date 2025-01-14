from tomobase.log import logger
from tomobase.registrations.environment import TOMOBASE_ENVIRONMENT
from tomobase.registrations.tiltschemes import TOMOBASE_TILTSCHEMES
from tomobase.registrations.processes import TOMOBASE_PROCESSES

from colorama import Fore, Style, init
import astra
import sys
import os


# Initialize colorama
init(autoreset=True)

def help(*args):
    """
    Help function for the library.
    
    Args:
        *args (strings): The arguments to pass to the help function can be None, 'environment', 'tiltschemes', 'processes', 'data'
    """ 
    #count number of arguements
    if len(args) == 0:
        args = ['environment', 'tiltschemes', 'processes', 'data']

    if args[0] is None:
        args = ['environment', 'tiltschemes', 'processes', 'data']

    for item in args:
        match item:
            case 'environment':
                msg = f"{Fore.GREEN}Environment Information:{Style.RESET_ALL}\n"
                msg += f"Python Version: {sys.version}\n"
                msg += f"Conda Environment: {os.environ.get('CONDA_DEFAULT_ENV', 'Not using Conda')}\n"
                msg += f"Pip Environment: {os.environ.get('VIRTUAL_ENV', 'Not using Pip virtual environment')}\n"

                msg += f"Astra Cuda Available: {astra.use_cuda()}\n"
                msg += f"Hyperspy Available: {TOMOBASE_ENVIRONMENT._hyperspy_available}\n"
                logger.info(msg)

            case 'tiltschemes':
                msg = f"{Fore.GREEN}TiltSchemes:{Style.RESET_ALL}\n"
                for key, value in TOMOBASE_TILTSCHEMES.items():
                    msg += f"{Fore.LIGHTCYAN_EX}{key}{Style.RESET_ALL}:\n"
                    msg += f"{value._controller.__doc__}\n"

                logger.info(msg)

            case 'processes':
                msg = f"{Fore.GREEN}Processes:{Style.RESET_ALL}\n"
                for key, value in TOMOBASE_PROCESSES.items():
                    msg += f"{Fore.LIGHTCYAN_EX}{key}{Style.RESET_ALL}:\n"
                    for key2, value2 in value.items():
                        msg += f"{Fore.MAGENTA}{key2}{Style.RESET_ALL}:\n"
                        msg += f"{value2._controller.__doc__}\n"
                logger.info(msg)

