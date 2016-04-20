#!/usr/bin/python3 -tt
"""
"""

import argparse
from glob import glob
import os
import shlex
import time
from shutil import copyfile
from subprocess import Popen
from pdb import set_trace


def remove_target(target, **options):
    """
        Remove "target" file. Provide meaningful feadback on the screen with verbose option.
    :param 'target': [str] path to the file to remove.
    :param 'verbose': [bool] Make it talk.
    :param 'debug': [bool] set_trace if exception was caught.
    :return: 0 - success. 1 - error.
    """
    filename = slice_path(target)
    try:
        os.remove(target)
        if options.get('verbose', False):
            print(' - Removing "%s"...' % (filename))
    except OSError as e:
        print (' - could not remove "%s"' % (filename))
        if options.get('debug', False):
            print ('- Entering debugging mode.')
            set_trace()
        return 1
    return 0


def symlink_target(source, target, **options):
    """
        Create symlink for target from the source. Provide meaningful feadback on the screen
    verbose option.
    :param 'source': [str] path to a file to create a symbolic link from.
    :param 'target': [str] path to the file to create a symbolic link to.
    :param 'verbose': [bool] Make it talk.
    :param 'debug': [bool] set_trace if exception was caught.
    :return: 0 - success. 1 - error.
    """
    src_filename = slice_path(source)
    target_filename = slice_path(target)
    try:
        os.symlink(source, target)
        if options.get('verbose', False):
            print(' - Creating a symlink from "%s" to "%s"...' % (src_filename, target_filename))
    except OSError as e:
        print (' - could not create a symlink of "%s" to "%s"!' % (src_filename, target_filename))
        if options.get('debug', False):
            print ('- Entering debugging mode.')
            set_trace()
        return 1
    return 0


def slice_path(target, slice_ratio=2):
    """
        Slice long path string on half (or by slice_ratio amount). Sometimes there is no need to print
    and absolute path to a string where the first N directories are irrelavent to the user.
        Example: /one/two/three/four/five/ will be sliced into three/four/five/.
    :param 'target': [str] path to slice.
    :param 'slice_ratio': [int or float](default=2) ratio by which to slice target.
                        e.g. len(target) / slice_ratio
    :return: [str] sliced target.
    """
    splited = target.split('/')
    length = int(len(splited) / slice_ratio)
    sliced = splited[length:]
    return '/'.join(sliced)


def cleanout_kernel(sys_img, **options):
    """
        Cleanout boot/vmlinuz* and boot/initrd.img/ files from the system image directory.
    These files are not needed for diskless boot and are just taking up extra space.
    :param 'sys_img': [str] path to the file system location to chroot to.
    :param 'verbose': [bool] Make it talk.
    :param 'debug': [bool] set_trace if exception was caught.
    :return: 0 - success. 1 - error.
    """
    boot_dir = '%s/boot/' % (sys_img)
    vmlinuz = glob('%s/vmlinuz*' % (boot_dir))      # Get list of vmlinuz and initrd files.
    initrd = glob('%s/initrd.img*' % (boot_dir))
    status = 0
    for target in vmlinuz + initrd:
        filename = os.path.basename(target)
        status = remove_target(target, **dict(options))
    return status


def configure_init(sys_img, **options):
    """

    :param 'verbose': [bool] Make it talk.
    :param 'debug': [bool] set_trace if exception was caught.
    :return: 0 - success. 1 - error.
    """
    new_init = os.path.join(sys_img, 'init')
    origin_init = '%s/sbin/init' % (sys_img)
    status = 0

    if os.path.exists(new_init):
        status = remove_target(new_init, **dict(options))

    status = symlink_target(origin_init, new_init, **dict(options))

    return status


def main(args):
    status = cleanout_kernel(args['sys_img'], verbose=args['verbose'], debug=args['debug'])
    status = configure_init(args['sys_img'], verbose=args['verbose'], debug=args['debug'])
    return status


if __name__ == '__main__':
    """
        TODO: Docstr
    """
    PARSER = argparse.ArgumentParser(description='Customize golden image on demand.')

    PARSER.add_argument('-i', '--sys-img',
                        help='Path to a file system image.',
                        default='/opt/hpetm/manifesting/sys-images/untar/')
    PARSER.add_argument('-M', '--manifest',
                        help='Path to a manifest.json file, which follows the manifesting API specs.',
                        default='')
    PARSER.add_argument('--verbose',
                        help='Make it talk.',
                        action='store_true')
    PARSER.add_argument('--debug',
                        help='Turn on debugging tool.',
                        action='store_true')
    ARGS, _ = PARSER.parse_known_args()
    main(vars(ARGS))
