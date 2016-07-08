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


def create_manifesting_env(config_path, ignore_list=['GOLDEN_IMAGE']):
    """
        Set manifesting environment in the right location (based of the config file),
    which follows ERS specs '8.3.1. OS Manifesting Data Storage'.
    """
    print(' ---- Creating manifest environment ---- ')
    from configs import manifest_config as cfg
    cfg.parameters.update(config_path)
    fields = cfg.parameters.manifest_env

    for field in fields:
        if field in ignore_list:
            continue
        path = cfg.parameters.__dict__[field]

        print(' - ' + path)
        create_folder(path)


def create_env(fields, ignore_list=[]):
    """
        Set manifesting environment in the right location (based of the config file),
    which follows ERS specs '8.3.1. OS Manifesting Data Storage'.
    """
    print(' ---- Creating manifest environment ---- ')

    for field in fields:
        if field in ignore_list:
            continue
        path = CONFIG.parameters.__dict__[field]

        print(' - ' + path)
        create_folder(path)



def create_tftp_env(config, ignore_list=[]):
    """
        Set TFTP environment by creating uppropriate folders in the location
    of manifesting api and running make_grub_config.py script to generate grub config
    files. Comply with ERS specs '8.3.1. OS Manifesting Data Storage'.
    """
    print(' ---- Creating manifest environment ---- ')
    '''
    for name, path in config.items():
        if name in ignore_list:
            continue
        print(' - ' + path)
        create_folder(path)
    '''
    from configs import manifest_config as cfg
    cfg.parameters.update(config_path)
    fields = cfg.parameters.tftp_env

    for field in fields:
        if field in ignore_list:
            continue
        path = cfg.parameters.__dict__[field]

        print(' - ' + path)
        create_folder(path)


def create_folder(path):
    """ A simple wrapper around os.makedirs that skip existed folders. """
    if not os.path.isdir(path):
        os.makedirs(path)


def parse_config_file(path):
    flask_obj = flask.Flask(__name__)
    flask_obj.config.from_pyfile(path)
    return flask_obj.config


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

    config_path = os.path.realpath(args['api_config'])
    config = parse_config_file(config_path)

    CONFIG.parameters.update(config_path)

    print()
    fields = CONFIG.parameters.manifest_env
    create_env(fields, ['GOLDEN_IMAGE'])

    print()
    fields = CONFIG.parameters.tftp_env
    create_env(fields)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Setup arguments that should not\
                                    be changed, unless you know what you doing.')
    parser.add_argument('--api-config',
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

