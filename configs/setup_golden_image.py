#!/usr/bin/python3 -tt
"""
    Generate a golden image using vmdebootstrap script that was slightly
modified for the needs of manifesting. Modified vmdebootstrap is in
./configs/ folder.  Note: "normal" vmdebootstrap must also be installed
on the system to satisfy package dependencies.
"""
import argparse
import os

from pdb import set_trace

# Imports are relative to parent directory with setup.py because implicit
# Python path "tmms" may not exist yet.

from configs.build_config import ManifestingConfiguration
from utils.utils import piper


def main(args):
    """
        Generate golden image into the manifesting work directory using
        vmdebootstrap.  Return None or raise error.
    """
    assert os.geteuid() == 0, 'This script requires root permissions'
    whereami = os.path.dirname(os.path.realpath(__file__))
    vmdebootstrap = whereami + '/vmdebootstrap'
    vmdconfig = whereami + '/filesystem/golden.arm.vmd'

    manconfig = ManifestingConfiguration(args.config, autoratify=False)
    missing = manconfig.ratify(dontcare=('GOLDEN_IMAGE', 'TMCONFIG'))
    destfile = manconfig['GOLDEN_IMAGE']    # now I can have a KeyError
    destdir = os.path.realpath(os.path.dirname(destfile))
    statvfs = os.statvfs(destdir)
    assert statvfs.f_bsize * statvfs.f_bavail > (10 * (1 << 30)), \
        'Need at least 10G on "%s"' % (destdir)

    cmd = '''%s --no-default-configs --hostname=GOLDEN
             --config=%s
             --mirror=%s''' % (
        vmdebootstrap,
        vmdconfig,
        manconfig['L4TM_MIRROR'])
    ret = piper(cmd, use_call=True)
    assert not ret, 'vmdebootstrap failed: %s' % stderr


if __name__ == '__main__':
    # Not worth working around this
    raise SystemExit('Can only be run from top-level setup.py')
