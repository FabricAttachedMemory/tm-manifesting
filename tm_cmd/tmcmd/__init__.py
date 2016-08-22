from pdb import set_trace

from shutil import get_terminal_size as terminal_size

from . import tm_package
from . import tm_task
from . import tm_sysimg
from . import tm_node
from . import tm_manifest


cmdlookup = {}

tmpkg = tm_package.TmPackage()
tmtask = tm_task.TmTask()
tmsysimg = tm_sysimg.TmSysImg()
tmnode = tm_node.TmNode()
tmmanifest = tm_manifest.TmManifest()

tmpkg.update_cmd(cmdlookup)
tmtask.update_cmd(cmdlookup)
tmsysimg.update_cmd(cmdlookup)
tmnode.update_cmd(cmdlookup)
tmmanifest.update_cmd(cmdlookup)


def set_help(func_dict):
    """
        Get dict of function names and its docstr passed in to the function as
    a dictionary.
    """
    result = {}
    for func_name, func in func_dict.items():
        if func.__doc__:
            result[func_name] = func.__doc__
    return result


def show_help(args=[], **options):
    """
        help

        Prints the synopsis and a list of the most commonly used commands.
    """
    help_dict = set_help(cmdlookup)
    help_size = len(help_dict)
    console_width = terminal_size().columns / 1.1
    console_space = (terminal_size().columns - console_width) / 2.3
    index = 0
    for func_name in sorted(help_dict.keys()):
        func_doc = help_dict[func_name]
        index += 1
        print(func_doc)
        if (index < help_size):
            print('{:>{}}*{:-<{}}*'.format(' ', console_space, '', console_width)) # make it pretty.
    return ''

cmdlookup['help'] = show_help
