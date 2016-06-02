#!/usr/bin/python3 -tt
"""
    TODO: Docstr
"""

import argparse
import os
import subprocess
import shlex


def main(args):
    """
        Generate golden image into the manifesting work directory using vmdebootstrap.
    """
    if os.getuid() != 0:
        raise RuntimeError('This script requires root permissions! (forgot sudo?)')

    if not os.path.isdir('/var/lib/tm-manifesting/sys-images/golden/'):
        raise RuntimeError('"tm-manifesting/sys-images/golden/" does not exist!')

    cmd = "python ./configs/vmdebootstrap \
            --owner=$LOGNAME --no-default-configs \
            --config=%s --hostname=pxe02" % (args['img_cfg'])
    cmd = shlex.split(cmd)
    status = subprocess.call(cmd)

    print('Done')
    return 0

if __name__ == '__main__':
    """
        TODO: Docstr
    """
    PARSER = argparse.ArgumentParser(description='Generate golden image on demand.')

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
    main(vars(ARGS))
