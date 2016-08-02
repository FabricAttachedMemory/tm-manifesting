#!/usr/bin/python3 -tt
import errno
import os
import sys


def make_dir(path):
    """
        A simple wrapper around os.makedirs that skip existing folders.
    :param 'path': [str] Leave this routine with a (new) directory at path
    :return: None or raised error
    """
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise RuntimeError('mkdir(%s) failed: %s' % (path, str(e)))


def make_symlink(source, target):
    '''
    Wrap os.symlink; succeed if target exists properly.  Used in setup.
    :param 'source': [str] path to a file to create a symbolic link from.
    :param 'target': [str] path to the file to create a symbolic link to.
    :return: 'None' on success or raise 'RuntimeError'
    '''

    print(' - symlink [%s] -> [%s]' % (source, target))
    try:
        os.symlink(source, target)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise RuntimeError('symlink(%s -> %s) failed: %s' % (
                source, target, str(e)))
        if not os.path.islink(target):
            raise RuntimeError('Existing "%s" is not a symlink' % target)
        if os.path.realpath(target) != source:
            raise RuntimeError(
                'Existing symlink "%s" does not point to %s' % (
                    target, source))


def basepath(fullpath, leading):
    '''Strip "leading" from "fullpath".  Certain restrictions may apply.'''
    for p in (fullpath, leading):
        assert p[0] == '/', '"%s" is not an absolute path' % p
    assert fullpath.startswith(leading), \
        '"%s" does not start with %s' % (fullpath, leading)
    tmp = fullpath[len(leading):]
    return tmp


def ratify(path):
    """
        Validate path (or list of path) exist on the system. Save each
    non-existing path and return it in a list in the end.

    :param 'path': [list or str] list of pathes to validate or a signle path.
    :return: [list] of non-existing pathes.
    """
    if not path:
        return []

    if not isinstance(path, list):
        path = [path]

    missing_path_list = []
    for to_validate in path:
        if not os.path.exists(to_validate):
            missing_path_list.append(to_validate)

    return missing_path_list


def ensure_pythonpath(cfg_hook, python_dest):
    """
        Validate the existance of the hook located in the python dist-packages
    that references the expected .pth hook config file. If not - create one.

    :param 'cfg_hook': full path to a .pth hook config file to use for an
                       environment path string.
    :param 'python_dest': path to python/dist-packages/ to place hook into.
    """
    hook_name = os.path.basename(cfg_hook)
    hooked_path = os.path.join(python_dest, cfg_hook)   # full path dest
    if os.path.exists(hooked_path):
        if os.readlink(hooked_path) == cfg_hook:        # is symlink correct?
            return

    os.symlink(cfg_hook, target)


def symlink_target(source, target):
    """
        Wrapper to os.symlink to trap errors.

        FIXME: THIS IS NOT IMPORTED ANYWHERE.  CAN IT BE DELETED?

    """
    try:
        os.symlink(source, target)
    except EnvironmentError as err:
        raise RuntimeError('Couldn\'t create a symlink: %s ' % err)
