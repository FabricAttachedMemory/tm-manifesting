#!/usr/bin/python3 -tt
import argparse
import os
import shlex
import subprocess
import sys

from pdb import set_trace

from tm_utils import wrappers


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

    wrappers.symlink_target(cfg_hook, tmms_pth)


def set_manifesting_env():
    """
        Set manifesting environment in the right location (based of the config file),
    which follows ERS specs '8.3.1. OS Manifesting Data Storage'.
    """
    raise NotImplemented('This is not the droid you are looking for. Not yet.. Not now...')


def set_tftp_env():
    """
        Set TFTP environment by creating uppropriate folders in the location
    of manifesting api and running make_grub_config.py script to generate grub config
    files. Comply with ERS specs '8.3.1. OS Manifesting Data Storage'.
    """
    raise NotImplemented('Not now!')


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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Setup arguments that should not\
                                    be changed, unless you know what you doing.')
    parser.add_argument('--python-hook-env',
                        help='dist-packages/ folder to use for the python environment.',
                        default='/usr/local/lib/python3.4/dist-packages/')
    parser.add_argument('--python-hook',
                        help='Path to a python\'s hook config file to use to put into' +\
                             '--python-hook-env',
                        default='configs/tmms.pth')
    args, _ = parser.parse_known_args()
    main(vars(args))

