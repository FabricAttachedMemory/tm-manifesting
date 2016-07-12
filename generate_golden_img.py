#!/usr/bin/python3 -tt
"""
    TODO: Docstr
"""

import argparse
import os
import subprocess
import shlex
from pdb import set_trace

from configs import build_config as CFG


def main(args):
    """
        Generate golden image into the manifesting work directory using
        vmdebootstrap.  Return None or raise error.
    """
    assert os.geteuid() == 0, 'This script requires root permissions'

    golden_dir = CFG.MANIFESTING_ROOT + '/sys-images/golden/'

    assert os.path.isdir(golden_dir), '"%s" does not exist' % (golden_dir)
    statvfs = os.statvfs(golden_dir)
    assert statvfs.f_bsize * statvfs.f_bavail > (4 * (1 << 30)), \
        'Need at least 4G on "%s"' % (golden_dir)

    cmd = '''./configs/vmdebootstrap --no-default-configs --hostname=GOLDEN
             --config=%s
             --mirror=%s''' % (
                args['img_cfg'],
                CFG.L4TM_MIRROR
             )
    cmd = shlex.split(cmd)
    status = subprocess.call(cmd)
    assert not status, 'vmdebootstrap failed: return status %s' % status

if __name__ == '__main__':
    """
        TODO: Docstr
    """
    PARSER = argparse.ArgumentParser(description='Generate golden image for nodes of The Machine.')

    PARSER.add_argument('-i', '--img-cfg',
                        help='A config file for your golden filesystem image that\
                        will be taken by vmdebootstrap.',
                        default='configs/filesystem/golden.arm.vmd')

    PARSER.add_argument('--verbose',
                        help='Make it talk.',
                        action='store_true')
    PARSER.add_argument('--debug',
                        help='Turn on debugging tool.',
                        action='store_true')
    ARGS, _ = PARSER.parse_known_args()

    errmsg = ''
    try:
        main(vars(ARGS))
    except AssertionError as e:
        errmsg = str(e)
    raise SystemExit(errmsg)
