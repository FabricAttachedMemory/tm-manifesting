#!/usr/bin/python3 -tt
"""
    Generate a golden image using vmdebootstrap script that was slightly
modified for the needs of manifesting. Modified vmdebootstrap is in
./configs/ folder.  Note: "normal" vmdebootstrap must also be installed
on the system to satisfy package dependencies.
"""
import argparse
import os
import subprocess
import shlex

from pdb import set_trace

from configs.build_config import ManifestingConfiguration


def main(config_file, config_vmd=None):
    """
        Generate golden image into the manifesting work directory using
        vmdebootstrap.  Return None or raise error.
    """
    assert os.geteuid() == 0, 'This script requires root permissions'

    manconfig = ManifestingConfiguration(config_file, autoratify=False)
    missing = manconfig.ratify(dontcare=('GOLDEN_IMAGE', 'TMCONFIG'))
    destfile = manconfig['GOLDEN_IMAGE']    # now I can have a KeyError
    destdir = os.path.realpath(os.path.dirname(destfile))
    statvfs = os.statvfs(destdir)
    assert statvfs.f_bsize * statvfs.f_bavail > (10 * (1 << 30)), \
        'Need at least 10G on "%s"' % (destdir)

    vmdebootstrap = os.path.realpath(__file__)
    vmdebootstrap = os.path.dirname(vmdebootstrap) + '/configs/vmdebootstrap'

    cmd = '''%s --no-default-configs --hostname=GOLDEN
             --config=%s
             --mirror=%s''' % (
                vmdebootstrap,
                config_vmd,
                manconfig['L4TM_MIRROR']
             )
    cmd = shlex.split(cmd)
    status = subprocess.call(cmd)
    assert not status, 'vmdebootstrap failed: return status %s' % status


if __name__ == '__main__':
    """
        Parse command line arguments and call main() function.
    """

    manconfig = ManifestingConfiguration

    parser = argparse.ArgumentParser(
        description='Generate golden image for nodes of The Machine.')
    ManifestingConfiguration.parser_add_config(parser)
    args, _ = parser.parse_known_args()

    parser.add_argument('--vmd',
                        help='(DEV ONLY) alternate vmdebootstrap config',
                        default=None)

    args, _ = parser.parse_known_args()
    print('Using config file', args.config)

    tmms_src_folder = os.path.realpath(__file__)
    tmms_src_folder = os.path.dirname(tmms_src_folder)

    if args.config is None:
        args.config = tmms_src_folder + '/manifest_config.py'

    if args.vmd is None:
        args.vmd = tmms_src_folder + '/configs/filesystem/golden.arm.vmd'

    errmsg = ''
    try:
        main(args.config, args.vmd)
    except AssertionError as e:
        errmsg = str(e)
    raise SystemExit(errmsg)
