#!/usr/bin/python3 --tt
"""
    Set of wrapper functinos that intent to provide\extend some custom functionality
based of the standard functions, e.g. error handling, throwing custom exceptions
and e.t.c.
"""
import os
import sys
from pdb import set_trace

_verbose = False


def symlink_target(source, target):
    """
        Create symlink for target from the source. Provide meaningful feadback on the screen
    verbose option.

    :param 'source': [str] path to a file to create a symbolic link from.
    :param 'target': [str] path to the file to create a symbolic link to.
    :param 'workdir': [str](default=None) path to change python working directory
                    to create symbolic link. Helpful to avoid relative path issue.
    :return: 'None' on success. Raise 'RuntimeError' on occurance of one of the 'EnvironmentError'.
    """
    try:
        if _verbose:
            print(' - Creating a symlink from "%s" to "%s"...' % (source, target))
        os.symlink(source, target)
    except EnvironmentError as err:
        raise RuntimeError ('Couldn\'t create a symlink: %s ' % err)
