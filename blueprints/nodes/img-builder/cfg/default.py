#!/usr/bin/python3 -tt
"""
"""

import argparse
from glob import glob
import json
import os
import shlex
import sys
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
    filename = slice_path(target)   # used only for prints.
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
        Set correct symbolic link to an /init/ file from /sbin/init

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


def cleanup_sources_list(sys_img, **options):
    """
        Check if /etc/apt/source.list.d/base.list file exists. If so, move it into
    /etc/apt/sources.list, cause base.list causing troubles.

    :param 'sys_img': [str] path to the file system location to chroot to.
    :param 'verbose': [bool] Make it talk.
    :param 'debug': [bool] set_trace if exception was caught.
    :return: 0 - success. 1 - error.
    """
    sources_list = '%s/etc/apt/sources.list' % sys_img
    sources_base = '%s/etc/apt/sources.list.d/base.list' % sys_img

    if not os.path.exists(sources_base):
        if options.get('verbose', False):
            print ('/etc/apt/sources.list.d/ is clean. Nothing to do here...')
        return 0
    if options.get('verbose', False):
        print (' - Copying "%s" file to "%s"' %
                (slice_path(sources_base), slice_path(sources_list)))
    copyfile(sources_base, sources_list)

    return remove_target(sources_base, **dict(options))


def set_hostname(sys_img, hostname, **options):
    """
        Set new hostname on the file system image. Get rid of the old hostname if it already exists
    and write a new one.

    :param 'sys_img': [str] path to the file system location to mess with.
    :param 'hostname': [str] hostname to be used for given system image.
    :param 'verbose': [bool] Make it talk.
    :return: 0 - success. 1 - error.
    """
    hostname_file = '%s/etc/hostname' % (sys_img)
    if os.path.exists(hostname_file):
        if remove_target(hostname_file, **dict(options)) == 1: # no need to continue if couldnt remove hostname file.
            return 1
    overwrite_file_content(hostname_file, hostname, **dict(options))
    return 0


def set_hosts(sys_img, content, **options):
    """
        Set new hostname on the file system image. Get rid of the old hostname if it already exists
    and write a new one.

    :param 'sys_img': [str] path to the file system location to mess with.
    :param 'hostname': [str] hostname to be used for given system image.
    :param 'verbose': [bool] Make it talk.
    :return: 0 - success. 1 - error.
    """
    hosts_file = '%s/etc/hosts' % (sys_img)
    if os.path.exists(hosts_file):
        if remove_target(hosts_file, **dict(options)) == 1: # no need to continue if couldnt remove hosts file.
            return 1
    overwrite_file_content(hosts_file, content, **dict(options))
    return 0


def overwrite_file_content(target, content, **options):
    """
        Overwrite file in the targeted location with a new content.

    :param 'target': [str] path to a file to create or overwrite with a new content
    :param 'content': [str] content to use in the new\overwritten file.
    :param 'verbose': [bool] Make it talk.
    """
    with open(target, 'w+') as file_obj:
        if options.get('verbose', False):
            print ('Writing into "%s": \n[\n%s\n]\n' % (target, content))
        file_content = '%s\n' % str(content)
        file_obj.write(file_content)


def main(args):
    with open(args['manifest']) as data_file:
        manifest = json.load(data_file)

    status = 0

    # if manifest.get('hostname', False):
    #     status = set_hostname(args['sys_img'], manifest['hostname'], verbose=args['verbose'], debug=args['debug'])
    #
    # if manifest.get('hosts', False):
    #     status = set_hosts(args['sys_img'], manifest['hosts'], verbose=args['verbose'], debug=args['debug'])

    status = cleanup_sources_list(args['sys_img'], verbose=args['verbose'], debug=args['debug'])

    # status = cleanout_kernel(args['sys_img'], verbose=args['verbose'], debug=args['debug'])
    # status = configure_init(args['sys_img'], verbose=args['verbose'], debug=args['debug'])
    return status


if __name__ == '__main__':
    """
        TODO: Docstr
    """
    PARSER = argparse.ArgumentParser(description='Customize golden image on demand.')

    PARSER.add_argument('-i', '--sys-img',
                        help='Path to a file system image.',
                        default='/opt/hpetm/manifesting/sys-images/untar/')
    PARSER.add_argument('-M', '--manifest', required=True,
                        help='Path to a manifest.json file, which follows the manifesting API specs.')
    PARSER.add_argument('--verbose',
                        help='Make it talk.',
                        action='store_true')
    PARSER.add_argument('--debug',
                        help='Turn on debugging tool.',
                        action='store_true')
    ARGS, _ = PARSER.parse_known_args()
    main(vars(ARGS))
