from pdb import set_trace

from . import tm_package
from . import tm_task


cmdlookup = {}

tmpkg = tm_package.TmPackage()
tmtask = tm_task.TmTask()

tmpkg.update_cmd(cmdlookup)
tmtask.update_cmd(cmdlookup)


def set_help(func_dict):
    """
        Get dict of function names and its docstr passed in to the function as
    a dictionary.
    """
    result = {}
    for func_name, func in func_dict.items():
        result[func.__name__] = func.__doc__
    return result


def show_help():
    """
    SYNOPSIS
        help

    DESCRIPTION
        Prints the synopsis and a list of the most commonly used commands.
    """
    help_dict = set_help(cmdlookup)
    help_size = len(help_dict)
    index = 0
    for func_name in sorted(help_dict.keys()):
        func_doc = help_dict[func_name]
        index += 1
        print(func_doc)
        if (index < help_size):
            print('{:>2}*{:-<75}*'.format(' ', '')) # make it pretty.
    return ''

cmdlookup['help'] = show_help
