#!/usr/bin/python3 -tt

import errno
import json
import os
import os.path
import shlex
import shutil
import subprocess
import sys

from pdb import set_trace

# Imports are relative to parent directory with setup.py because implicit
# Python path "tmms" may not exist yet.

from configs.build_config import ManifestingConfiguration
from utils.utils import make_dir


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
    - create folders for PXE server (dnsmasq)
    """
    if not args.packaging:
        print(' ---- Installing base packages ---- ')
        install_base_packages()

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


if __name__ == '__main__':
    # Not worth working around this
    raise SystemExit('Can only be run from top-level setup.py')
