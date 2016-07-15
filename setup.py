#!/usr/bin/python3 -tt
import argparse
import os
import json
import shlex
import shutil
import subprocess
import sys

from pdb import set_trace

from configs import build_config
from utils import utils


def set_python_path(hook_dest):
    """
        Set PYTHONPATH environment by creating a symlink fron tmms.pth file to the
    'path'/tmms.pth. Python interpreter then will pick it up and append path included
    in the tmmms.pth file.

    :param 'hook_dest': path to where to place python config hook file. Usually,
                    or by default in this function, it's: /usr/local/lib/python3.4/dist-packages/
    """
    manifest_module_path = ['/tm-manifest/', '.', '/unittests/']
    generated_path = []
    for path in manifest_module_path:
        this_file = os.path.dirname(os.path.realpath(__file__))
        norm_path = os.path.normpath(this_file + '/' + path)
        generated_path.append(norm_path)

    if os.path.exists(hook_dest):
        print('PYTHONPATH alread set. Overwritting...')

    with open(hook_dest, 'w') as file_obj:
        file_obj.write('\n'.join(generated_path))


def _create_env(fields, ignore_list=[]):
    """
        Create folder tree based of the list of fileds passed, that must comply
    with config/build_config/ structure. This function dependent on build_config/ 
    module and its  variables naming convention.

    :param 'fields': [list] variable names that determines path values of the
                    manifesting entities.
    :param 'ignore_list': [list] of fields to ignore, e.g. GOLDEN_IMAGE
    """
    print(' ---- Creating manifest and tftp environment ---- ')
    for field in fields:
        if field in ignore_list:
            continue
        path = build_config.settings[field]

        print(' - ' + path)
        create_folder(path)


def create_grub_env(tmconfig):
    """
        Create grub environment under manfiesting /tftp/ folder.
    :param 'tmconfig': path to the hpetmconfig.json file
    """
    raise NotImplemented('No soup for you... for now.')


def create_folder(path):
    """ A simple wrapper around os.makedirs that skip existed folders. """
    if not os.path.isdir(path):
        os.makedirs(path)


def main(args):
    """
        Run all the functions needed to setup tm-manifesting environment:
    - set PYTHONPATH using .pth file that have a path to the manifesting/ source code.
    - create folders for manifesting server and manifesting tftp based of the config file
    - run make_grub_cfg.py script to create grub config files in the tftp folder
    - run generate_golden_image.py script to generate golden image
    """
    assert os.geteuid() == 0, 'This script requires root permissions'
    set_python_path(args['python_hook'])

    config_path = os.path.realpath(args['config'])

    build_config.make_config(config_path)

    print()
    fields = build_config._manifest_env
    _create_env(fields, ['GOLDEN_IMAGE'])

    print()

    fields = build_config._tftp_env
    _create_env(fields)
    print()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Setup arguments that should not\
                                    be changed, unless you know what you doing.')
    parser.add_argument('-c', '--config',
                        help='A config.py file to be used by manifesting server.',
                        default='./manifest_config.py')

    parser.add_argument('-C', '--tmconfig',
                        help='A config file that stores nodes topology.',
                        default='configs/hpetmconfig.py')

    parser.add_argument('-p', '--python-hook',
                        help='dist-packages/ folder to use for the python environment.',
                        default='/usr/local/lib/python3.4/dist-packages/tmms.pth')

    args, _ = parser.parse_known_args()
    main(vars(args))

