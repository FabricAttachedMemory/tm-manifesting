#!/usr/bin/python3 -tt

import argparse
import errno
import json
import os
import os.path
import shlex
import shutil
import subprocess
import sys

from pdb import set_trace

from utils import utils

from configs import build_config

S_IFLNK = os.path.stat.S_IFLNK


def set_python_lib():
    """
        Create a symlink to manifesting source code to:
    /usr/local/lib/python3.4/dist-packages/tmms so that user could import
    manifesting libraries as follows: import tmms.unittests.
    setup.py must be at top of manifesting repo tree.
    """
    py_ver = 'python%d.%d' % (sys.version_info.major, sys.version_info.minor)
    paths_to_lib = ('/usr/local/lib/%s/dist-packages' % py_ver,
                    '/%s/lib/%s/dist-packages' % (sys.prefix, py_ver))

    manifesting_path = os.path.realpath(__file__)
    manifesting_path = os.path.dirname(manifesting_path)
    for path in paths_to_lib:
        if path not in sys.path:
            break

        path = path + '/tmms'
        print(' - symlink [%s] -> [%s]' % (path, manifesting_path))
        try:
            os.symlink(manifesting_path, path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise RuntimeError('symlink() failed: %s' % str(e))
            if os.lstat(path).st_mode & S_IFLNK != S_IFLNK:
                raise RuntimeError('Existing "%s" is not a symlink' % path)
            if os.path.realpath(path) != manifesting_path:
                raise RuntimeError(
                    'Existing "%s" symlink does not point to %s' % (
                        path, manifesting_path))
    else:
        raise RuntimeError(
            'Can\'t find suitable path in python environment to link tmms!')


def _create_env(fields, ignore_list=[]):
    """
        Create folder tree based of the list of fields passed, that must comply
    with config/build_config/ structure. This function dependent on build_config/
    module and its  variables naming convention.

    :param 'fields': [list] variable names that determines path values of the
                    manifesting entities.
    :param 'ignore_list': [list] of fields to ignore, e.g. GOLDEN_IMAGE
    """
    for field in fields:
        if field in ignore_list:
            continue
        path = build_config.settings[field]

        print(' - ' + path)
        create_folder(path)


def create_folder(path):
    """ A simple wrapper around os.makedirs that skip existed folders. """
    try:
        if not os.path.isdir(path):
            os.makedirs(path)
    except OSError:
        raise RuntimeError('Failed to create %s' % (path))


def install_packages():
    """
        Install packages required by manifesting service.  It only needs
        files from tm-librarian, it won't actually get run from here.
    """
    pkg_list = ['apt-utils', 'vmdebootstrap',
                'python3-flask', 'python3-requests',
                'python3-debian', 'tm-librarian']
    try:
        errors = []
        for pkg in pkg_list:
            cmd = 'apt-get install -y -qq %s' % (pkg)
            cmd = shlex.split(cmd)
            process = subprocess.Popen(cmd, stderr=subprocess.PIPE)
            output, err = process.communicate()
            if process.returncode != 0:
                errors.append('[%s] %s' % (pkg, err.decode()))
        if errors:
            raise RuntimeError('\n'.join(errors))
    except subprocess.CalledProcessError as e:
        raise RuntimeError('"%s" failed: %s' % (cmd, str(e)))


def main(args):
    """
        Run all the functions needed to setup tm-manifesting environment:
    - install dependent packages (this setup script is a workaround)
    - introduce a tmms package to Python environment via symlink
    - create folders for manifesting files and DBs
    - create folders for TFTP server (dnsmasq)
    - run make_grub_cfg.py script to populate grub config files under TFTP
    """
    assert os.geteuid() == 0, 'This script requires root permissions'
    assert sys.platform == 'linux'

    print(' ---- Installing dependent L4TM packages ---- ')
    install_packages()

    config_path = os.path.realpath(args['config'])

    print(' ---- Creating workaround Python package path ---- ')
    set_python_lib()

    print(' ---- Creating manifest environment ---- ')
    build_config.make_config(config_path)
    fields = build_config._manifest_env
    _create_env(fields, ['GOLDEN_IMAGE'])
    golden_img_dir = os.path.dirname(build_config.settings['GOLDEN_IMAGE'])
    create_folder(golden_img_dir)

    print(' ---- Creating TFTP environment ---- ')
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

    args, _ = parser.parse_known_args()
    errmsg = ''     # establish scope
    try:
        main(vars(args))
        raise SystemExit(0)
    except RuntimeError as err:
        errmsg = str(err)
    except Exception as err:
        errmsg = 'UNEXPECTED ERROR: %s' % str(err)

    raise SystemExit('%s\nsetup failed' % errmsg)
