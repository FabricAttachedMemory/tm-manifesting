#!/usr/bin/python3 -tt

import errno
import json
import os
import os.path
import shutil
import sys

from pdb import set_trace

# Imports are relative to parent directory with setup.py because implicit
# Python path "tmms" may not exist yet.

from configs.build_config import ManifestingConfiguration
from utils.utils import piper, create_loopback_files
from utils.file_utils import make_dir, remove_target


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
    print(' ---- Adding ARM64 architecture via apt-get update ---- ')
    for cmd in (
        'dpkg --add-architecture arm64',
        'apt-get update',
        'apt-get -y --force-yes upgrade',
        'apt-get -y --force-yes dist-upgrade'
    ):
        ret, stdout, stderr = piper(cmd)
        assert not (bool(ret) or bool(stderr)), \
            '"%s" failed: %s' % (cmd, stderr)

    print(' ---- Installing base packages ---- ')
    pkg_list = ['apt-utils', 'cpio', 'dnsmasq',
                'dosfstools', 'grub-efi-arm64-bin',
                'python3-debian', 'python3-dnspython', 'python3-flask',
                'python3-netaddr', 'python3-netifaces', 'python3-requests',
                'qemu-efi', 'tm-librarian', 'vmdebootstrap']
    errors = []
    for pkg in pkg_list:
        cmd = 'apt-get install -y -qq %s' % (pkg)
        ret, stdout, stderr = piper(cmd)
        if ret or stderr:
            if pkg == 'tm-librarian':       # might be on plain-old Debian
                try:
                    import tm_librarian     # maybe it's already there
                except ImportError:
                    print(
                        '%s not loaded, symlink it into Python from git' % pkg,
                        file=sys.stderr)
            elif pkg in ('qemu-efi', ):     # might be on plain-old Debian
                print('Need manual installation of %s !!!!!!!!!!!!!!!!!', pkg)
            else:
                errors.append('[%s] %s' % (pkg, stderr))
    if errors:
        raise RuntimeError('\n'.join(errors))


def main(args):
    """
        Run all the functions needed to setup tm-manifesting environment:
    - install dependent packages (this setup script is a workaround)
    - introduce a tmms package to Python environment via symlink
    - create folders for manifesting files and DBs
    - create folders for PXE server (dnsmasq)
    """
    if not args.packaging:
        install_base_packages()

    print(' ---- Loading config file "%s" ---- ' % args.config)
    manconfig = ManifestingConfiguration(args.config, autoratify=False)

    print(' ---- Creating manifest environment ---- ')
    fields = manconfig.manifesting_keys
    _create_env(manconfig, fields, ignore=('GOLDEN_IMAGE',))   # It's a file
    golden_img_dir = os.path.dirname(manconfig['GOLDEN_IMAGE'])
    make_dir(golden_img_dir)

    print(' ---- Creating TFTP environment ---- ')
    # Need to remove the TFTP_IMAGES directory first.   We don't want
    # leftover, stale bound nodes confusing commands if this is a re-run
    # after a change to /etc/tmconfig with a different node list.
    remove_target(manconfig['TFTP_IMAGES'])
    fields = manconfig.tftp_keys
    _create_env(manconfig, fields)
    print()

    create_loopback_files()


if __name__ == '__main__':
    # Not worth working around this
    raise SystemExit('Can only be run from top-level setup.py')
