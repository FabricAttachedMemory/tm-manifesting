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

# Imports are relative because implicit Python path "tmms" may not exist yet.

from configs.build_config import ManifestingConfiguration

from utils.utils import make_dir, make_symlink


def link_into_python():
    """
        Create a symlink to THIS manifesting source tree under the known
    Python hierarchy so that user could import manifesting libraries like
    "import tmms.foobar".  Keep it simple.  setup.py must be at the top.
    """
    py_ver = 'python%d.%d' % (sys.version_info.major, sys.version_info.minor)
    tmptuple = (sys.prefix, py_ver)
    paths_to_lib = ('%s/local/lib/%s/dist-packages' % tmptuple,
                    '%s/lib/%s/dist-packages' % tmptuple)

    setup_file = os.path.realpath(__file__)
    repo_path = os.path.dirname(setup_file)
    for path in paths_to_lib:
        if path not in sys.path:
            break
        path = path + '/tmms'
        make_symlink(repo_path, path)
    else:
        raise RuntimeError(
            'Can\'t find suitable path in python environment to link tmms!')


def _create_env(manconfig, fields, ignore=None):
    """
        Create folder tree from passed parameters that must comply with
    config/build_config/ structure. This function depends on build_config
    module and its variables naming convention.

    :param 'fields': [list] variable names that determines path values of the
                    manifesting entities.
    :param 'ignore': (tuple) of fields to ignore, e.g. ('GOLDEN_IMAGE', )
    """

    if ignore is None:
        ignore = ()
    for field in fields:
        if field in ignore:
            continue
        path = manconfig[field]

        print(' - ' + path)
        make_dir(path)


def install_base_packages():
    """
        Install packages required by manifesting service.  It only needs
        files from tm-librarian, it won't actually get run from here.
    """
    pkg_list = ['apt-utils', 'vmdebootstrap', 'grub-efi-arm64-bin',
                'dnsmasq', 'python3-dnspython',
                'python3-netaddr', 'python3-netifaces',
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
    # Before reading the config file, satisfy some preconditions
    assert os.geteuid() == 0, 'This script requires root permissions'
    assert sys.platform == 'linux'

    if not args.packaging:
        print(' ---- Creating workaround Python package path ---- ')
        link_into_python()

    print(' ---- Loading config file "%s" ---- ' % args.config)
    manconfig = ManifestingConfiguration(args.config, autoratify=False)

    print(' ---- Creating manifest environment ---- ')
    fields = manconfig.manifesting_keys
    _create_env(manconfig, fields, ignore=('GOLDEN_IMAGE',))   # It's a file
    golden_img_dir = os.path.dirname(manconfig['GOLDEN_IMAGE'])
    make_dir(golden_img_dir)

    print(' ---- Creating TFTP environment ---- ')
    fields = manconfig.tftp_keys
    _create_env(manconfig, fields)
    print()


def add_cmdline_args(parser):
    '''Can be included by super-script "setup.py"'''
    parser.add_argument(
        '-P', '--packaging',
        help='This flag should only be set by post-setup scripts in Debian ' +
             'installer. Using it while trying to run from the git repo ' +
             'will result in a non-functioning environment.\n',
        action='store_true')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Setup arguments intended for tmms developers only')
    add_cmdline_args(parser)

    # A fresh L4TM may not have some things, including flask.
    # Chicken-and-egg: flask is needed to parse config file

    args, _ = parser.parse_known_args()
    if not args.packaging:
        print(' ---- Installing base packages ---- ')
        install_base_packages()

    ManifestingConfiguration.parser_add_config(parser)
    args, _ = parser.parse_known_args()
    print('Using config file', args.config)

    errmsg = ''     # establish scope
    try:
        main(args)
        raise SystemExit(0)
    except (AssertionError, RuntimeError, ValueError) as err:
        errmsg = str(err)
    except Exception as err:
        errmsg = 'UNEXPECTED ERROR: %s' % str(err)

    raise SystemExit('%s\nsetup failed' % errmsg)
