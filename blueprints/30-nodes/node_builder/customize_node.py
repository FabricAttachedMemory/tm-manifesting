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
from shutil import copyfile, rmtree, copytree
from subprocess import Popen
from pdb import set_trace

_verbose = None     # Poor man's class
_debug = None


def copy_target_into(target, into, **options):
    """
        Wraper around shutil.copyfile function. Main intention is to catch a spevifiec
    exception and raise RuntimeError with a meaningfull message. Also, provides
    debugging and verbose options.

    :param 'target': [str] path to an object that needs to be coppied.
    :param 'into': [str] path to the destination object (include destinatino file
                  in the path, e.g. dest/file.name)
    :return: 'None' on success. Raise 'RuntimeError' on occurance of one of the 'EnvironmentError'.
    """
    try:
        if options.get('verbose', False):
            print(' - Copying "%s" into "%s"...' % (target, into))
        if os.path.isdir(target):
            copytree(target, into) # copy directory
        else:
            copyfile(target, into) # copy single file
    except EnvironmentError as err:
        if options.get('debug', False):
            print ('- Entering <func copy_target_into> debugging mode.')
            set_trace()
        raise RuntimeError ('Couldn\'t copy "%s" into "%s"! [%s]' % (target, into, err))


def remove_target(target, **options):
    """
        Remove "target" file. Provide meaningful feadback on the screen with verbose option.

    :param 'target': [str] path to the file to remove.
    :param 'verbose': [bool] Make it talk.
    :param 'debug': [bool] set_trace if exception was caught.
    :return: 'None' on success. Raise 'RuntimeError' on occurance of one of the 'EnvironmentError'.
    """
    filename = slice_path(target)   # used only for prints.
    try:
        if options.get('verbose', False):
            print(' - Removing "%s"...' % (filename))
        if os.path.isdir(target):
            rmtree(target)      # remove directory tree
        else:
            os.remove(target)   # remove single file
    except EnvironmentError as e:
        if options.get('debug', False):
            print ('- Entering debugging mode.')
            set_trace()
        raise RuntimeError ('Couldn\'t remove "%s"!' % (filename))


def symlink_target(source, target, **options):
    """
        Create symlink for target from the source. Provide meaningful feadback on the screen
    verbose option.

    :param 'source': [str] path to a file to create a symbolic link from.
    :param 'target': [str] path to the file to create a symbolic link to.
    :param 'verbose': [bool] Make it talk.
    :param 'debug': [bool] set_trace if exception was caught.
    :return: 'None' on success. Raise 'RuntimeError' on occurance of one of the 'EnvironmentError'.
    """
    src_filename = slice_path(source)
    target_filename = slice_path(target)
    try:
        if options.get('verbose', False):
            print(' - Creating a symlink from "%s" to "%s"...' % (src_filename, target_filename))
        os.symlink(source, target)
    except EnvironmentError as e:
        if options.get('debug', False):
            print ('- Entering <func symlink_target> debugging mode.')
            set_trace()
        raise RuntimeError ('Couldn\'t create a symlink from "%s" to "%s"!' % (src_filename, target_filename))


def write_to_file(target, content, **options):
    """
        Overwrite file in the targeted location with a new content.

    :param 'target': [str] path to a file to create or overwrite with a new content
    :param 'content': [str] content to use in the new\overwritten file.
    :param 'verbose': [bool] Make it talk.
    """
    try:
        with open(target, 'w+') as file_obj:
            if options.get('verbose', False):
                print ('Writing into "%s": \n[\n%s\n]\n' % (target, content))
            file_content = '%s\n' % str(content)
            file_obj.write(file_content)
    except EnvironmentError:
        if options.get('debug', False):
            print ('- Entering <func write_to_file> debugging mode.')
            set_trace()
        raise RuntimeError ('Couldn\'t overwrite file "%s"!' % (target))


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
    :return: 'None' on success. Raise 'RuntimeError' on occurance of one of the 'EnvironmentError'.
    """
    boot_dir = '%s/boot/' % (sys_img)
    vmlinuz = glob('%s/vmlinuz*' % (boot_dir))      # Get list of vmlinuz and initrd files.
    initrd = glob('%s/initrd.img*' % (boot_dir))
    # copy kernel files into destination location (outside of sys_img)
    try:
        for kernel in vmlinuz+initrd:
            copy_into = os.path.basename(kernel)
            copy_target_into(kernel, '%s/%s' % (kernel_dest, copy_into) )

        for target in vmlinuz + initrd:
            filename = os.path.basename(target)

    except RuntimeError as err:
        if options.get('debug', False):
            print ('- Entering <func cleanout_kernel> debugging mode.')
            set_trace()
        raise RuntimeError ('Errror occured while cleaning kernel!\n\
                            %s' % (err))


def fix_init(sys_img, **options):
    """
        Set correct symbolic link to an /init/ file from /sbin/init

    :param 'verbose': [bool] Make it talk.
    :param 'debug': [bool] set_trace if exception was caught.
    :return: 'None' on success. Raise 'RuntimeError' on occurance of one of the 'EnvironmentError'.
    """
    new_init = os.path.join(sys_img, 'init')
    origin_init = '%s/sbin/init' % (sys_img)

    try:
        if os.path.exists(new_init):
            remove_target(new_init, **dict(options))
        symlink_target(origin_init, new_init, **dict(options))
    except RuntimeError as err:
        if options.get('debug', False):
            print ('- Entering <func fix_init> debugging mode.')
        raise RuntimeError('Error occured while fixing /init file!\n\
                            %s' % (err))


def cleanup_sources_list(sys_img, **options):
    """
        Check if /etc/apt/source.list.d/base.list file exists. If so, move it into
    /etc/apt/sources.list, cause base.list causing troubles.

    :param 'sys_img': [str] path to the file system location to chroot to.
    :param 'verbose': [bool] Make it talk.
    :param 'debug': [bool] set_trace if exception was caught.
    :return: 'None' on success. Raise 'RuntimeError' on occurance of one of the 'EnvironmentError'.
    """
    sources_list = '%s/etc/apt/sources.list' % sys_img
    sources_base = '%s/etc/apt/sources.list.d/base.list' % sys_img

    if not os.path.exists(sources_base):
        if options.get('verbose', False):
            print ('/etc/apt/sources.list.d/ is clean. Nothing to do here...')
            return None
    try:
        copy_target_into(sources_base, sources_list)
        remove_target(sources_base, **dict(options))
    except RuntimeError as err:
        if options.get('debug', False):
            print ('- Entering <func cleanup_sources_list> debugging mode.')
            set_trace()
        raise RuntimeError('Error occured while cleaning sources.list!\n\
                            %s' % (err))


def set_hostname(sys_img, hostname, **options):
    """
        Set new hostname on the file system image. Get rid of the old hostname if it already exists
    and write a new one.

    :param 'sys_img': [str] path to the file system location to mess with.
    :param 'hostname': [str] hostname to be used for given system image.
    :param 'verbose': [bool] Make it talk.
    :return: 'None' on success. Raise 'RuntimeError' on occurance of one of the 'EnvironmentError'.
    """
    hostname_file = '%s/etc/hostname' % (sys_img)
    try:
        if os.path.exists(hostname_file):
            remove_target(hostname_file, **dict(options))
        write_to_file(hostname_file, hostname, **dict(options))
    except RuntimeError as err:
        raise RuntimeError ('Error occured while setting hostname!\n\
                            %s' % (err))


def set_hosts(sys_img, hostname, **options):
    """
        Set new hostname on the file system image. Get rid of the old hostname if it already exists
    and write a new one.

    :param 'sys_img': [str] path to the file system location to mess with.
    :param 'hostname': [str] hostname to be used for given system image.
    :param 'verbose': [bool] Make it talk.
    :return: 'None' on success. Raise 'RuntimeError' on occurance of one of the 'EnvironmentError'.
    """
    hosts_file = '%s/etc/hosts' % (sys_img)
    try:
        if os.path.exists(hosts_file):
            remove_target(hosts_file, **dict(options))

        content = []                                # To ensure correct text alignment
        content.append('127.0.0.1   localhost')     # treat each element as a line in /etc/hosts
        content.append('127.1.0.1   %s' % hostname) #
        content = '\n'.join(content)                # then join it into a string of lines.

        write_to_file(hosts_file, content, **dict(options))
    except RuntimeError as err:
        raise RuntimeError ('Error occured while setting hosts content!\n\
                            %s' % (err))


def untar(target, destination=None, **options):
    """
        Untar target file into the same folder of the tarball.

    :param 'target': [str] path to a .tar file to untar.
    :return: [str] path to untared content.
    """
    if destination is None:
        destination = os.path.dirname(target)
        destination = os.path.normpath('%s/untar/' % destination)

    try:
        if options.get('verbose', False):
            print(' - Uncompressing "%s" into "%s"...' % (targer, destination))
        with tarfile.open(target) as tar_obj:
            tar_obj.extractall(path=destination)
    except (tarfile.ReadError, tarfile.ExtractError) as err:
        remove_target(destination)  # cleanup on error.
        raise RuntimeError ('Error occured while untaring "%s"! [%s]' % (target,err))

    return destination


def create_cpio(target, destination, **options):
    """
        Get the bootable pieces: initrd CPIO and a kernel.

    :param 'target': [str] path to an untared filesystem img to create .cpio from.
    :param 'destination': [str] path to the folder to save .cpio file to.
    :return: returncode of Popen() process.
    """
    cpio_name = destination.split('/')[-1]
    cpio_script = os.path.join(os.path.dirname(__file__), 'cpio.sh')
    cmd = 'sudo %s %s %s' % (cpio_script, target, destination)
    cmd = shlex.split(cmd)
    hasError = [] # store error message and error object of caught exception.
    try:
        if options.get('verbose', False):
            print(' - Creating "%s/cpio.sh" from "%s"... ' % (destination, target))
        status = Popen(cmd)
        status.communicate()
    except subprocess.CalledProcessError as err:
        hasError[0] = ('Error occured while creating cpio of %s!\n\
                    [%s]' % (err))
        hasError[1] = err

    if hasError:
        if options.get('verbose', False):
            print('Error occured while creating cpio!', file=sys.stderr)
        if options.get('debug', False):
            print ('- Entering <func untar> debugging mode.')
            set_trace()
        raise RuntimeError(hasError[0])

def execute(sys_img, **kwargs):
    """
        TODO: docstr
    """
    global _verbose, _debug

    _verbose = kwargs['verbose']
    _debug = kwargs['debug']
    response = {}
    response['status'] = 'success'  # Nothing happened yet! Let's keep it this way...
    response['message'] = 'System image was created!'

    #  It is OK to have a big exception block, because individual exception handling
    # is done inside those functions that would through RuntimeError (most of the
    # time).
    try:
        # Setting hostname and hosts...
        set_hostname(sys_img, kwargs['hostname'])
        set_hosts(sys_img, kwargs['hostname'])

        # Fixing sources.list
        cleanup_sources_list(sys_img)
        # Cleaning up kernel
        kernel_dest = sys_img.split('/')
        kernel_dest = '/'.join(kernel_dest[:len(kernel_dest)-1])
        kernel_dest = '%s/' % (kernel_dest)
        cleanout_kernel(sys_img, kernel_dest)
        # Symlink /init
        fix_init(sys_img)

        dest = os.path.dirname(sys_img)
        # Create .cpio file from untar.
        create_cpio(sys_img, dest)

        # Remove untar'ed, modified fileimage folder
        remove_target(sys_img)
    except RuntimeError as err:
         response['status'] = 'error'
         response['message'] = 'Ouch! Runtime error! We expected that...\n[%s]' % (err)
    except Exception as err:    # Its OK. Don't want Flask to through any traceback at user.
        exc_type, _, exc_tb = sys.exc_info()
        response['status'] = 'error'
        response['message'] = 'Aye! Did not expect that!\n\
                                [Error: %s]\n\
                                [Line: %s]\n\
                                [File: %s]' % \
                                (exc_type, exc_tb.tb_lineno, os.path.basename(__file__))
    return response
