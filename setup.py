#!/usr/bin/python3 -tt
import argparse
import os
import json
import flask
import shlex
import shutil
import subprocess
import sys

from pdb import set_trace

from configs import manifest_config as CONFIG
from utils import utils


def set_python_path(cfg_hook, hook_dist):
    """
        Set PYTHONPATH environment by creating a symlink fron tmms.pth file to the
    'path'/tmms.pth. Python interpreter then will pick it up and append path included
    in the tmmms.pth file.

    :param 'cfg_hook': path to the python's dist-packages (or site-packages) to set
                  tmms.pth into.
    :param 'hook_dit': path to where to place python config hook file. Usually,
                    or by default in this function, it's: /usr/local/lib/python3.4/dist-packages/
    """
    tmms_pth_file = os.path.basename(cfg_hook)        # name of the .pth file to
    tmms_pth = os.path.join(hook_dist, tmms_pth_file) # create a simpling destination.
    if os.path.exists(tmms_pth):
        print('PYTHONPATH alread set. Overwritting...')
        os.remove(tmms_pth)

    utils.symlink_target(cfg_hook, tmms_pth)


def _create_env(fields, ignore_list=[]):
    """
        Create folder tree based of the list of fileds passed, that must comply
    with config/manifest_config/ structure. This function dependent on manifest_config/ 
    module and its  variables naming convention.

    :param 'fields': [list] variable names that determines path values of the
                    manifesting entities.
    :param 'ignore_list': [list] of fields to ignore, e.g. GOLDEN_IMAGE
    """
    print(' ---- Creating manifest and tftp environment ---- ')
    for field in fields:
        if field in ignore_list:
            continue
        path = CONFIG.parameters.__dict__[field]

        print(' - ' + path)
        create_folder(path)


def create_folder(path):
    """ A simple wrapper around os.makedirs that skip existed folders. """
    if not os.path.isdir(path):
        os.makedirs(path)


def main(args):
    """
        Run all the functions needed to setup tm-manifesting environment:
    - set PYTHONPATH using .pth file that have a path to the manifesting/ source code.
    -
    """

    args['python_hook_env'] = os.path.realpath(args['python_hook_env'])
    args['python_hook'] = os.path.realpath(args['python_hook'])

    assert os.geteuid() == 0, 'This script requires root permissions'
    set_python_path(args['python_hook'], args['python_hook_env'])

    config_path = os.path.realpath(args['config'])
    set_trace()

    CONFIG.parameters.update(config_path)

    print()
    fields = CONFIG.parameters.manifest_env
    _create_env(fields, ['GOLDEN_IMAGE'])

    print()

    fields = CONFIG.parameters.tftp_env
    _create_env(fields)
    print()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Setup arguments that should not\
                                    be changed, unless you know what you doing.')
    parser.add_argument('--config',
                        help='A config.py file to be used by manifesting server.',
                        default='configs/manifest_config/default.py')

    parser.add_argument('--python-hook-env',
                        help='dist-packages/ folder to use for the python environment.',
                        default='/usr/local/lib/python3.4/dist-packages/')

    parser.add_argument('--python-hook',
                        help='Path to a python\'s hook config file to use to put into' +\
                             '--python-hook-env',
                        default='configs/tmms.pth')

    args, _ = parser.parse_known_args()
    main(vars(args))

