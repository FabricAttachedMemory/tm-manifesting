#!/usr/bin/python3 -tt
"""
- Copyright 2016 Hewlett Packard Enterprise Development Company LP

    Script that performs a basic set of customizations of a golden image:
 - Move kernel from [filesystem_image]/boot/ (not needed for diskless boot)
 - Set correct symbolic link for /init file
 - Set /etc/hostname
 - Set /etc/hosts
 - and some other operations.  
"""

import argparse
from glob import glob
import json
import os
import tarfile
import shlex
import sys
import time
from shutil import copyfile, rmtree
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
        if os.path.isdir(target):
            rmtree(target)
        else:
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


def cleanout_kernel(sys_img, kernel_dest, **options):
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
    # copy kernel files into destination location (outside of sys_img)
    for kernel in vmlinuz+initrd:
        copy_into = os.path.basename(kernel)
        if options.get('verbose', False):
            print(' - Copying "%s" into "%s"' % (kernel, slice_path(copy_into)) )        
        copyfile(kernel, '%s/%s' % (kernel_dest, copy_into) )

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


def untar(target, **options):
    """
        Untar target file into the same folder of the tarball.

    :param 'target': [str] path to a .tar file to untar.
    :return: [str] path to untared content.
    """
    if not tarfile.is_tarfile(target):
        return target

    tar = tarfile.open(target)
    destination = os.path.dirname(target)
    destination = os.path.normpath('%s/untar/' % destination)

    if options.get('verbose', False):
        print (' * Extracting "%s" into "%s"' % (target, destination))
    if not os.path.isdir(destination):
        os.mkdir(destination)

    tar.extractall(path=destination)
    tar.close()
    return destination


def tar_folder(target, destination, **options):
    """
        Tar targeted folder into destination file.
    :param 'target': [str] path to a folder to be tared.
    :param 'destination': [str] path to a folder to save .tar file to.
    :return: 0 - success. 1 - error.
    """
    if os.path.exists(destination):
        remove_target(destination, **dict(options))

    try:
        tar = tarfile.open(destination, mode='w')
    except IOError as err:
        if options.get('verbose', False):
            print(' ~ Could not open %s flie! Error: %s ' % (target, err))
        return 1

    if options.get('verbose', False):
        print (' * Compressing "%s" into "%s"...' % (target, destination))

    # compress everything in the targeted location into a tarball.
    for dirname in glob('%s/' % target):
        to_tar = os.path.normpath(dirname).split('/')[-1]
        tar.add(target, arcname=dirname)

    tar.close()

    return 0


def create_cpio(target, destination, **options):
    """
        Get the bootable pieces: initrd CPIO and a kernel.
    :param 'target': [str] path to an untared filesystem img to create .cpio from.
    :param 'destination': [str] path to the folder to save .cpio file to.
    :return: returncode of Popen() process.
    """
    cpio_name = destination.split('/')[-1]
    cmd = 'sudo ./cpio.sh %s %s' % (target, destination)
    
    if options.get('verbose', False):
        print(' - Creating "%s/cpio.sh" from "%s"... ' % (destination, target))

    cmd = shlex.split(cmd)
    status = Popen(cmd)
    status.communicate()

    return status.returncode


def execute(manifest, sys_img_tar, **args):
    # Untar filesystem image
    args['verbose'] = args.get('verbose', False)
    args['debug'] = args.get('debug', False)

    sys_img = untar(sys_img_tar, verbose=args['verbose'])

    with open(manifest) as data_file:
        manifest = json.load(data_file)

    status = 0

    # Setting hostname...
    if manifest.get('hostname', False):
        status = set_hostname(sys_img, manifest['hostname'], verbose=args['verbose'], debug=args['debug'])

    # Setting hosts... 
    if manifest.get('hosts', False):
        status = set_hosts(sys_img, manifest['hosts'], verbose=args['verbose'], debug=args['debug'])

    # Fixing sources.list
    status = cleanup_sources_list(sys_img, verbose=args['verbose'], debug=args['debug'])
    # Cleaning up kernel
    kernel_dest = sys_img.split('/')                                # DON't like this. Should be re-thought
    kernel_dest = '/'.join(kernel_dest[:len(kernel_dest)-1])
    kernel_dest = '%s/' % (kernel_dest)
    status = cleanout_kernel(sys_img, kernel_dest, verbose=args['verbose'], debug=args['debug'])
    # Symlink /init
    status = configure_init(sys_img, verbose=args['verbose'], debug=args['debug'])

    # Compress target into .tar format
    status = tar_folder(sys_img, sys_img_tar,  verbose=['verbose'])

    dest = os.path.dirname(sys_img_tar)
    # Create .cpio file from untar.
    create_cpio(sys_img, dest, verbose=args['verbose'], debug=args['debug'])

    # Remove untar'ed, modified fileimage folder
    remove_target(sys_img, verbose=args['verbose'], debug=args['debug'])

    if status == 1:
        remove_target()

    return status


def main(args):
    """
        Perform a "common" set of operations on the filesystem image to 
    prepare it to boot on the node. 
    """
    return execute(args['manifest'], args['sys_img'], verbose=args['verbose'], debug=args['debug'])

if __name__ == '__main__':
    """
        Argument Parser routine.
    """
    PARSER = argparse.ArgumentParser(description='Customize golden image on demand.')

    PARSER.add_argument('-i', '--sys-img',
                        help='Path to a file system image folder.',
                        required=True)
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
