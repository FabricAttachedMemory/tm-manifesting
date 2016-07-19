#!/usr/bin/python3 -tt
"""
    Generate a golden image using vmdebootstrap script that was slightly modified
for the needs of this script. Modified vmdebootstrap is in ./configs/ folder.
Note: vmdebootstrap must be installed on the system in order for this script to work.
"""
import argparse
import os
import subprocess
import shlex


def main(args):
    """
        Generate golden image into the manifesting work directory using
        vmdebootstrap.  Return None or raise error.
    """
    assert os.geteuid() == 0, 'This script requires root permissions'

    assert os.path.isdir(args['dest']), '"%s" does not exist' % (args['dest'])
    statvfs = os.statvfs(args['dest'])
    assert statvfs.f_bsize * statvfs.f_bavail > (4 * (1 << 30)), \
        'Need at least 4G on "%s"' % (args['dest'])

    cmd = '''./configs/vmdebootstrap --no-default-configs --hostname=GOLDEN
             --config=%s
             --mirror=%s''' % (
                args['img_cfg'],
                args['mirror']
             )
    cmd = shlex.split(cmd)
    status = subprocess.call(cmd)
    assert not status, 'vmdebootstrap failed: return status %s' % status


if __name__ == '__main__':
    """
        Parse command line arguments and call main() function.
    """
    PARSER = argparse.ArgumentParser(description='Generate golden image for nodes of The Machine.')

    PARSER.add_argument('-i', '--img-cfg',
                        help='A config file for your golden filesystem image that\
                        will be taken by vmdebootstrap.',
                        default='configs/filesystem/golden.arm.vmd')

    PARSER.add_argument('-d', '--dest',
                        help='Destination to save the image into')

    PARSER.add_argument('-m', '--mirror',
                        help='Repo Mirror to create image from.',
                        default='http://hlinux-deejay.us.rdlabs.hpecorp.net/l4tm')

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
