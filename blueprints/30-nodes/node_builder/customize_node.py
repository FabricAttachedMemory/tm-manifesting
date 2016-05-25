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
from subprocess import Popen, PIPE, CalledProcessError
from pdb import set_trace

_verbose = None     # Poor man's class
_debug = None


def copy_target_into(target, into):
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
        if _verbose:
            print(' - Copying "%s" into "%s"...' % (target, into))
        if os.path.isdir(target):
            copytree(target, into) # copy directory
        else:
            copyfile(target, into) # copy single file
    except EnvironmentError as err:
        raise RuntimeError ('Couldn\'t copy "%s" into "%s"! [%s]' % (target, into, err))


def remove_target(target):
    """
        Remove "target" file. Provide meaningful feadback on the screen with verbose option.

    :param 'target': [str] path to the file to remove.
    :param 'verbose': [bool] Make it talk.
    :param 'debug': [bool] set_trace if exception was caught.
    :return: 'None' on success. Raise 'RuntimeError' on occurance of one of the 'EnvironmentError'.
    """
    filename = slice_path(target)   # used only for prints.
    try:
        if _verbose:
            print(' - Removing "%s"...' % (filename))
        if os.path.isdir(target):
            rmtree(target)      # remove directory tree
        else:
            os.remove(target)   # remove single file
    except EnvironmentError as e:
        raise RuntimeError ('Couldn\'t remove "%s"!' % (filename))


def symlink_target(source, target, workdir=None):
    """
        Create symlink for target from the source. Provide meaningful feadback on the screen
    verbose option.

    :param 'source': [str] path to a file to create a symbolic link from.
    :param 'target': [str] path to the file to create a symbolic link to.
    :param 'workdir': [str](default=None) path to change python working directory
                    to create symbolic link. Helpful to avoid relative path issue.
    :return: 'None' on success. Raise 'RuntimeError' on occurance of one of the 'EnvironmentError'.
    """
    if workdir is not None:
        os.chdir(workdir)

    src_filename = slice_path(source)
    target_filename = slice_path(target)
    try:
        if _verbose:
            print(' - Creating a symlink from "%s" to "%s"...' % (src_filename, target_filename))
        os.symlink(source, target)
    except EnvironmentError as e:
        raise RuntimeError ('Couldn\'t create a symlink from "%s" to "%s"!' % (src_filename, target_filename))


def write_to_file(target, content):
    """
        Overwrite file in the targeted location with a new content.

    :param 'target': [str] path to a file to create or overwrite with a new content
    :param 'content': [str] content to use in the new\overwritten file.
    :param 'verbose': [bool] Make it talk.
    """
    try:
        with open(target, 'w+') as file_obj:
            if _verbose:
                print ('Writing into "%s": \n[\n%s\n]\n' % (target, content))
            file_content = '%s\n' % str(content)
            file_obj.write(file_content)
    except EnvironmentError:
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


def cleanout_kernel(sys_img, kernel_dest):
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
            remove_target(kernel)
    except RuntimeError as err:
        raise RuntimeError ('Errror occured while cleaning kernel!\n\
                            %s' % (err))


def fix_init(sys_img):
    """
        Set correct symbolic link to an /init/ file from /sbin/init

    :param 'verbose': [bool] Make it talk.
    :param 'debug': [bool] set_trace if exception was caught.
    :return: 'None' on success. Raise 'RuntimeError' on occurance of one of the 'EnvironmentError'.
    """
    new_init = os.path.join(sys_img, 'init')
    try:
        if os.path.exists(new_init):
            remove_target(new_init)
        symlink_target('sbin/init', 'init', sys_img)
    except (RuntimeError, EnvironmentError) as err:
        raise RuntimeError('Error occured while fixing /init file!\n\
                            %s' % (err))


def cleanup_sources_list(sys_img):
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
        if _verbose:
            print ('/etc/apt/sources.list.d/ is clean. Nothing to do here...')
        return None
    try:
        copy_target_into(sources_base, sources_list)
        remove_target(sources_base)
    except RuntimeError as err:
        raise RuntimeError('Error occured while cleaning sources.list!\n\
                            %s' % (err))


def set_hostname(sys_img, hostname):
    """
        Set new hostname on the file system image. Get rid of the old hostname if it already exists
    and write a new one.

    :param 'sys_img': [str] path to the file system location to mess with.
    :param 'hostname': [str] hostname to be used for given system image.
    :return: 'None' on success. Raise 'RuntimeError' on occurance of one of the 'EnvironmentError'.
    """
    hostname_file = '%s/etc/hostname' % (sys_img)
    try:
        if os.path.exists(hostname_file):
            remove_target(hostname_file)
        write_to_file(hostname_file, hostname)
    except RuntimeError as err:
        raise RuntimeError ('Error occured while setting hostname!\n\
                            %s' % (err))


def set_hosts(sys_img, hostname):
    """
        Set new hostname on the file system image. Get rid of the old hostname if it already exists
    and write a new one.

    :param 'sys_img': [str] path to the file system location to mess with.
    :param 'hostname': [str] hostname to be used for given system image.
    :return: 'None' on success. Raise 'RuntimeError' on occurance of one of the 'EnvironmentError'.
    """
    hosts_file = '%s/etc/hosts' % (sys_img)
    try:
        if os.path.exists(hosts_file):
            remove_target(hosts_file)

        content = []                                # To ensure correct text alignment
        content.append('127.0.0.1   localhost')     # treat each element as a line in /etc/hosts
        content.append('127.1.0.1   %s' % hostname) #
        content = '\n'.join(content)                # then join it into a string of lines.

        write_to_file(hosts_file, content)
    except RuntimeError as err:
        raise RuntimeError ('Error occured while setting hosts content!\n\
                            %s' % (err))


def untar(target, destination=None):
    """
        Untar target file into the same folder of the tarball.

    :param 'target': [str] path to a .tar file to untar.
    :return: [str] path to untared content.
    """
    if destination is None:
        destination = os.path.dirname(target)
        destination = os.path.normpath('%s/untar/' % destination)

    try:
        if _verbose:
            print(' - Uncompressing "%s" into "%s"...' % (target, destination))
        with tarfile.open(target) as tar_obj:
            tar_obj.extractall(path=destination)
    except (tarfile.ReadError, tarfile.ExtractError) as err:
        raise RuntimeError ('Error occured while untaring "%s"! [%s]' % (target,err))

    return destination


def create_cpio(target, destination):
    """
        Get the bootable pieces: initrd CPIO and a kernel.

    :param 'target': [str] path to an untared filesystem img to create .cpio from.
    :param 'destination': [str] path to the folder to save .cpio file to.
    :return: returncode of Popen() process.
    """
    try:
        if _verbose:
            print(' - Creating "%s/cpio.sh" from "%s"... ' % (destination, target))
        cmd = 'find %s -not -name vmlinuz -not -name initrd.img \
                -path ./boot -prune -o -print' % (target)
        cmd = shlex.split(cmd)
        find_sh = Popen(cmd, stdout=PIPE)
        cmd = 'sudo cpio --create --format \'newc\''
        cmd = shlex.split(cmd)
        with open(destination, 'w+') as file_obj:
            cpio_sh = Popen(cmd, stdin=find_sh.stdout, stdout=file_obj)

        cpio_sh.communicate()
        find_sh.communicate()
    except CalledProcessError as err:
        raise RuntimeError('Error occured while creating cpio from "%s"\
                            ["%s"]' % (target, err))


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

        dest = '%s/%s.cpio' % (os.path.dirname(sys_img), kwargs['hostname'])
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
