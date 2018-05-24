#!/usr/bin/python3 -tt
"""
  This script sets up the environment for the manifesting to be functional based
of the tmms (/etc/tmms) values. It will also install several required packages.
"""
__author__ = "Rocky Craig, Zakhar Volchak"
__copyright__ = "Copyright 2017 Hewlett Packard Enterprise Development LP"
__maintainer__ = "Rocky Craig, Zakhar Volchak"
__email__ = "rocky.craig@hpe.com, zakhar.volchak@hpe.com"


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
from utils import core_utils
from utils import file_utils



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
        file_utils.make_dir(path)


def install_base_packages():
    """
        Install packages required by manifesting service.  It only needs
        files from tm-librarian, it won't actually get run from here.
    """
    ret, stdout, stderr = core_utils.piper('dpkg --print-foreign-architectures')
    if 'arm64' not in stdout.decode():
        print(' ---- Adding ARM64 architecture via apt-get ---- ')
        for cmd in (
            'dpkg --add-architecture arm64',
            'apt-get -y update',
        ):
            ret, stdout, stderr = core_utils.piper(cmd)
            assert not (bool(ret) or bool(stderr)), \
                '"%s" failed: %s' % (cmd, stderr)

    print(' ---- Installing base packages ---- ')
    this_file = os.path.abspath(__file__)
    this_folder = os.path.dirname(this_file)
    pkg_list = read_requirements_list(this_folder + '/packages.req')

    errors = []
    for pkg in pkg_list:
        if not pkg or pkg.startswith('#') or pkg.startswith('//'):
            continue
        print( '- Attempting to install package: %s ' % (pkg))
        cmd = 'apt-get install -y -qq %s' % (pkg)
        ret, stdout, stderr = core_utils.piper(cmd)
        if ret or stderr:
            if pkg == 'tm-librarian':       # might be on plain-old Debian
                try:
                    import tm_librarian     # maybe it's already there
                except ImportError:
                    print(
                        '%s not loaded, symlink it into Python from git' % pkg,
                        file=sys.stderr)
            elif pkg in ('qemu-efi', ):     # might be on plain-old Debian
                print('Need manual installation of %s' % pkg)
            else:
                error_msg_str = '[%s] %s' % (pkg, stderr)
                # Vmdebootstrap logs this message to stderr for some reason,
                # even though it is not an error...
                if 'Extracting templates from packages' in error_msg_str:
                    continue
                errors.append(error_msg_str)
    if errors:
        raise RuntimeError('\n'.join(errors))


def read_requirements_list(path):
    """
        Read a file with package names (one per ine) to be installed.
    """
    file_content = ''
    with open(path, 'r') as file_obj:
        file_content = file_obj.read().rstrip('\n')
    return file_content.split('\n')


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
    file_utils.make_dir(golden_img_dir)

    print(' ---- Creating TFTP environment ---- ')
    # Need to remove the TFTP_IMAGES directory first.   We don't want
    # leftover, stale bound nodes confusing commands if this is a re-run
    # after a change to /etc/tmconfig with a different node list.
    file_utils.remove_target(manconfig['TFTP_IMAGES'])
    fields = manconfig.tftp_keys
    _create_env(manconfig, fields)
    print()

    core_utils.create_loopback_files()


if __name__ == '__main__':
    # Not worth working around this
    raise SystemExit('Can only be run from top-level setup.py')
