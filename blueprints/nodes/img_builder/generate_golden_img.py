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
        TODO: Docstr.
    """
    if os.getuid() != 0:
        raise EnvironmentError('This script requires root permissions! (forgot sudo?)')

    cmd = "python ./vmdebootstrap.py \
            --owner=$LOGNAME --no-default-configs \
            --config=%s --hostname=pxe02" % (args['img_cfg'])
    cmd = shlex.split(cmd)
    status = subprocess.Popen(cmd)

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
                        default='/opt/hpetm/manifesting/img.cfg/golden.vmd')

    PARSER.add_argument('--verbose',
                        help='Make it talk.',
                        action='store_true')
    PARSER.add_argument('--debug',
                        help='Turn on debugging tool.',
                        action='store_true')
    ARGS, _ = PARSER.parse_known_args()
    main(vars(ARGS))
