#!/usr/bin/python3 -tt
"""
    Generate a golden image using vmdebootstrap script that was slightly
modified for the needs of manifesting. Modified vmdebootstrap is in
./configs/ folder.  Note: "normal" vmdebootstrap must also be installed
on the system to satisfy package dependencies.
"""
import argparse
import errno
import os

from pdb import set_trace

# Imports are relative to parent directory with setup.py because implicit
# Python path "tmms" may not exist yet.

from configs.build_config import ManifestingConfiguration
from utils.file_utils import remove_target
from utils.utils import piper, create_loopback_files


def main(args):
    """
        Generate golden image into the manifesting work directory using
        vmdebootstrap.  Return None or raise error.
    """
    assert os.geteuid() == 0, 'This script requires root permissions'
    create_loopback_files()     # LXC containers don't have them on restart.

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

    vmdlog = destdir + '/vmdebootstrap.log'
    vmdimage = destdir + '/golden.arm.img'
    cmd = '''%s --no-default-configs
             --config=%s
             --log=%s
             --image=%s
             --tarball=%s
             --mirror=%s
             --distribution=%s
          ''' % (
        vmdebootstrap,
        vmdconfig,
        vmdlog,
        vmdimage,
        destfile,
        manconfig['L4TM_MIRROR'],
        manconfig['L4TM_RELEASE'])

    os.chdir(destdir)   # The embedded debootstrap drogs a log file here.
    remove_target(destdir + '/debootstrap.log')
    remove_target(vmdlog)
    ret, _, _ = piper(cmd, use_call=True)     # Watch it all go by
    assert not ret, 'vmdebootstrap failed: %s:' % (errno.errorcode[ret])


if __name__ == '__main__':
    # Not worth working around this
    raise SystemExit('Can only be run from top-level setup.py')
