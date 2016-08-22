#!/usr/bin/python3
import os
import shutil
import sys

_allowed_dirs = [
				['var', 'lib'],
				['var', 'tmp'],
				['tmp']
				]

def _fs_sanity_check(target):
    """
        Some file routines are HORRIBLY dangerous to run as root.
    Perform a few idiot checks.
    :param 'target': [str] path about to be copied/moved/overwritten/removed
    :return: 'None' on success. Raise 'AssertionError' on problems.
    """
    if os.geteuid():    # Not root?  Trust the FS
        return
    target = target.strip()
    assert target[0] == '/', 'Not an absolute path'
    elems = target.split('/')[1:]   # zeroth is empty string
    assert len(elems) > 2, 'Target is a primary directory'
    assert elems[:2] == ['var', 'lib'], 'Target is not under /var/lib'


def copy_target_into(target, into):
    """
        Wrapper around shutil.copy* functions. Main intention is to catch a
    specific exception and raise RuntimeError with a meaningful message. Also
    provides debugging and verbose options.

    :param 'target': [str] path to an object that needs to be copied.
    :param 'into': [str] path to the destination object (dir path or filename)
    :return: 'None' on success. Raise 'RuntimeError' on problems.
    """
    try:
        if _verbose:
            print(' - Copying "%s" into "%s"...' % (target, into))
        _fs_sanity_check(target)
        if os.path.isdir(target):
            shutil.copytree(target, into)   # copy directory
        else:
            shutil.copyfile(target, into)   # copy single file
    except (AssertionError, RuntimeError, EnvironmentError) as err:
        raise RuntimeError('Couldn\'t copy "%s" into "%s": %s' % (
            target, into, str(err)))