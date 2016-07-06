#!/urs/bin/python3 -tt
import os

from . import wrappers


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

    wrappers.symlink_target(cfg_hook, hooked_path)
