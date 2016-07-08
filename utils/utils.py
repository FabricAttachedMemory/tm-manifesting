#!/urs/bin/python3 -tt
import os
import sys


def ratify(path):
    """
        Validate path (or list of path) exist on the system. Save each non-existing
    path and return it in a list in the end.

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
    that is pointed to the expected .pth hook config file. If not - create one.

    :param 'cfg_hook': full path to a .pth hook config file to use for a python
                       environment path string.
    :param 'python_dest': path to python/dist-packages/ to place hook into.
    """
    hook_name = os.path.basename(cfg_hook)
    hooked_path = os.path.join(python_dest, cfg_hook)   # full path destination for
                                                        # hook to place into.
    if os.path.exists(hooked_path):
        if os.readlink(hooked_path) == cfg_hook:    # check if symlink is correct
            return

    os.symlink(cfg_hook, target)


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