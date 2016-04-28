#!/usr/bin/python3 -tt
"""
"""
import argparse
import os
import shlex
import time
from shutil import copyfile
from subprocess import Popen
from pdb import set_trace


def main(args):
    cfg_name = os.path.basename(args['config'])
    cfg_destination = os.path.join(args['sys_img'], cfg_name)

    copyfile(args['config'], cfg_destination)

    os.chmod(cfg_destination, 64)   # set execution bits only.


    cmd = "sudo chroot %s bash %s" % (args['sys_img'], cfg_name)
    cmd = shlex.split(cmd)
    status = Popen(cmd)
    print("Doing work...")
    status.communicate()

    cfg_to_remove = os.path.join(args['sys_img'], cfg_name)
    os.remove(cfg_to_remove)
    return 0


if __name__ == '__main__':
    """
        TODO: Docstr
    """
    PARSER = argparse.ArgumentParser(description='Customize golden image on demand.')

    PARSER.add_argument('--config',
                        help='Config file to use for file system customization.',
                        default='./cfg/default.sh')
    PARSER.add_argument('-i', '--sys-img',
                        help='Path to a file system image.',
                        default='/opt/hpetm/manifesting/sys-images/untar/')
    PARSER.add_argument('--verbose',
                        help='Make it talk.',
                        action='store_true')
    PARSER.add_argument('--debug',
                        help='Turn on debugging tool.',
                        action='store_true')
    ARGS, _ = PARSER.parse_known_args()
    main(vars(ARGS))
