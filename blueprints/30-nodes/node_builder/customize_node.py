#!/usr/bin/python3
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
import gzip
import json
import os
import tarfile
import shutil   # explicit namespace differentiates from our custom FS routines
import sys
import time

from pdb import set_trace

from tmms.utils.utils import find, piper, untar
from tmms.utils.file_utils import copy_target_into, remove_target, make_symlink
from tmms.utils.file_utils import write_to_file, workdir

_verbose = None     # Poor man's class
_debug = None

#==============================================================================


def cleanout_kernel(target_dir, sys_img):
    """
        Remove boot/vmlinuz* and boot/initrd.img/ files from new file system.
    These files are not needed for diskless boot.  Move them to target_dir
    for future use.

    :param 'kernel_dest': [str] where to move the unecessary files.
    :param 'sys_img': [str] where to find the unecessary files.
    :return: 'None' on success. Raise 'RuntimeError' on problems.
    """
    boot_dir = '%s/boot/' % (sys_img)
    vmlinuz = glob('%s/vmlinuz*' % (boot_dir))      # one list
    initrd = glob('%s/initrd.img*' % (boot_dir))    # two lists
    try:
        for source in vmlinuz + initrd:            # move them all
            # FIXME: we need a move
            copy_into = os.path.basename(source)
            copy_target_into(source, '%s/%s' % (target_dir, copy_into))
            remove_target(source)
        # I want to return the kernel I found and moved.   In an error
        # condition (such as one of the unit tests) it may not be there.
        vmlinuz = glob('%s/vmlinuz*' % (target_dir))
        return vmlinuz[0] if vmlinuz else None
    except Exception as err:
        raise RuntimeError('Errror occured cleanout_kernel(): %s' % str(err))


def fix_init(sys_img):
    """
        Set correct symbolic link to a chrooted /init file from /sbin/init

    :param 'verbose': [bool] Make it talk.
    :param 'debug': [bool] set_trace if exception was caught.
    :return: 'None' on success. Raise 'RuntimeError' on problems.
    """
    try:
        with workdir(sys_img):      # At the root
            if os.path.exists('init'):
                os.unlink('init')
            make_symlink('sbin/init', 'init')
    except RuntimeError as err:      # Expecting this error from make_symlink,
        raise RuntimeError(str(err)) # therefore, let it print the err message
    except Exception as err:
        raise RuntimeError('Unexpected error in fix_init function: %s' % str(err))

#==============================================================================
# setup_golden_image leaves a UUID-based mount that fails.  Also, FIXME
# rootfs needs some kind of TLC to show up in df.


def fix_rootfs(sys_img):
    try:
        with workdir(sys_img):      # At the root
            with open('etc/fstab', 'w') as f:    # no leading slash!!!
                f.write('proc /proc proc defaults 0 0\n')
    except Exception as e:
        raise RuntimeError('Error occured while fixing rootfs: %s' % str(e))

#==============================================================================


def cleanup_sources_list(sys_img):
    """
        Check if /etc/apt/source.list.d/base.list file exists. If so, move it
    into /etc/apt/sources.list, because base.list is causing collisions.

    :param 'sys_img': [str] path to the file system location to chroot to.
    :return: 'None' on success. Raise 'RuntimeError' on problems.
    """
    sources_list = '%s/etc/apt/sources.list' % sys_img
    sources_base = '%s/etc/apt/sources.list.d/base.list' % sys_img

    if not os.path.exists(sources_base):
        if _verbose:
            print('/etc/apt/sources.list.d/ is clean. Nothing to do here...')
        return None

    sources_updated = set_sources_areas(
        sources_base, ['main', 'contrib', 'non-free'])

    try:
        remove_target(sources_base)
        remove_target(sources_list)
        write_to_file(sources_list, sources_updated)
    except RuntimeError as err:
        raise RuntimeError('Error occured while cleaning sources.list!\n\
                            %s' % (err))


def set_sources_areas(sources_list, areas):
    """
        Set mirror areas in the sources.list, e.g each line that starts with
    'deb' will be modified the end of its line to provided "areas":
    deb http://l4tm.mirror cattleprod main --> areas = ['non-free', 'contrib']
    deb http://l4tm.mirror cattleprod non-free contrib

    :param 'sources_list': [str] path to a sources.list file to be modified.
    :param 'areas': [list] of areas to be set ['main', 'contrib', 'non-free']
    :return: [str] modified sources.list content.
    """
    file_content = None
    with open(sources_list, 'r') as file_obj:
        file_content = file_obj.read()

    sources_updated = []
    for line in file_content.split('\n'):
        if not line.startswith('deb'):
            sources_updated.append(line)
            continue
        mirror = line.split(' ')[:3]
        mirror.extend(['main', 'contrib', 'non-free'])
        sources_updated.append(' '.join(mirror))

    return '\n'.join(sources_updated)

#==============================================================================


def set_client_id(sys_img, client_id):
    """
        Augment dhclient configuration file

    :param 'sys_img': [str] path to the file system location to mess with.
    :param 'hostname': [str] hostname to be used for given system image.
    :return: 'None' on success. Raise 'RuntimeError' on problems.
    """
    dhclient_conf = '%s/etc/dhcp/dhclient.conf' % (sys_img)
    try:
        with open(dhclient_conf, 'a') as f:
            f.write('\nsend dhcp-client-identifier "%s";\n' % client_id)
    except Exception as err:
        raise RuntimeError('Cannot set DHCP client ID: %s' % str(err))

#==============================================================================


def set_hostname(sys_img, hostname):
    """
        Set new hostname on the file system image.

    :param 'sys_img': [str] path to the file system location to mess with.
    :param 'hostname': [str] hostname to be used for given system image.
    :return: 'None' on success. Raise 'RuntimeError' on problems.
    """
    hostname_file = '%s/etc/hostname' % (sys_img)
    try:
        if os.path.exists(hostname_file):
            remove_target(hostname_file)
        write_to_file(hostname_file, hostname)
    except RuntimeError as err:
        raise RuntimeError('Cannot set /etc/hostname: %s' % str(err))


def set_hosts(sys_img, hostname):
    """
        Set new /etc/hosts on the file system image.

    :param 'sys_img': [str] path to the file system location to mess with.
    :param 'hostname': [str] hostname to be used for given system image.
    :return: 'None' on success. Raise 'RuntimeError' on problems.
    """
    hosts_file = '%s/etc/hosts' % (sys_img)
    try:
        if os.path.exists(hosts_file):
            remove_target(hosts_file)

        content = []
        content.append('127.0.0.1   localhost')     # visual alignment
        content.append('127.1.0.1   %s' % hostname)
        content = '\n'.join(content)

        write_to_file(hosts_file, content)
    except RuntimeError as err:
        raise RuntimeError('Cannot set /etc/hosts: s' % str(err))


def create_cpio(dest_file, src_dir):
    """
        Get the non-boot pieces, ignoring initrd, kernel, and /boot.

    :param 'dest_file': [str] path to save cpio archive
    :param 'src_dir': [str] folder to create .cpio from.
    :return: returncode of Popen() process.
    """
    try:
        if _verbose:
            print(' - Creating %s from %s... ' % (dest_file, src_dir))

        # FIXME: do a test to insure dest_dir is not a subdir of src_dir

        # Skip things even though they may have been moved
        found_data = find(
            src_dir,
            ignore_files=['vmlinuz', 'initrd.img'],
            ignore_dirs=['boot'])

        cmd = 'cpio --create --format \'newc\''
        cpio_stdin = '\n'.join(found_data).encode()  # needed for Popen pipe.

        with open(dest_file, 'w') as dest_obj:
            # create CPIO relative to the 'find' path, to avoid '/' in archive
            # names.  Note: searching outside of  untar folder results in a
            # "full path" string (e.g. whatever/untar/boot...., instead
            # ./boot...). This causes Kernel Panic when trying to boot with
            # such a cpio file.
            with workdir(src_dir):
                ret, cpio_out, cpio_err = piper(
                    cmd, stdin=cpio_stdin, stdout=dest_obj)
                assert not ret, 'cpio failed: %s' % cpio_err

        # output find data to a log file
        if _verbose:
            with open('/tmp/man_find.log', 'w') as file_obj:
                file_obj.write('\n'.join(found_data))   # FIXME proper logging

    except Exception as err:
        raise RuntimeError('Couldn\'t create "%s" from "%s": %s' % (
            dest_file, src_dir, str(err)))


#==============================================================================


def install_packages(sys_img, pkg_list, task_list):
    """
        Install list of packages into the filesystem image.
    Function will generate a bash script with lines of "apt-get install"
    in it.   This script is placed under the file system. Then, this function
    will execute this script under the chrooted to "sys_img". Also,
    every action performed by generated install.sh script is logged into the
    'sys_img + "/manifesting.log"' file.

    :param 'sys_img': [str] path to filesystem image to install packages to.
    :param 'pkg_list': [list] of packages to be installed.
    """
    if _verbose:
        print(' - Installing %s... ' % pkg_list)

    script_header = """#!/bin/bash
# Created %s
set -ue
exec > /install.log 2>&1  # /tmp/ is cleaned out of boot
apt-get update
apt-get upgrade --assume-yes
apt-get dist-upgrade --assume-yes
""" % time.ctime()
    script_file = sys_img + '/install.sh'
    with open(script_file, 'w') as file_obj:
        file_obj.write(script_header)

        file_obj.write('\n# Packages: %s\n' % pkg_list)
        if pkg_list is not None:
            for pkg in pkg_list.split(','):
                cmd = 'apt-get install --assume-yes %s\n' % pkg
                file_obj.write(cmd)

        file_obj.write('\n# Tasks: %s\n' % task_list)
        if task_list is not None:
            for task in task_list.split(','):
                cmd = 'tasksel install %s\n' % task
                file_obj.write(cmd)

    os.chmod(script_file, 0o744)

    try:
        cmd = '/usr/sbin/chroot %s %s ' % (sys_img, '/install.sh')
        # This can take MINUTES.  "album" pulls in about 80 dependent packages.
        # While running, sys_image/install.log is updated.  That could be
        # tail followed and status updated, MFT' time.
        ret, _, _ = piper(cmd, use_call=True)
        assert not ret, 'chroot failed: errno %d' % (ret)
    except Exception as err:
        raise RuntimeError('Couldn\'t install packages: %s' % str(err))

#==============================================================================

def update_status(args, message, status='building'):
    """
        status must be one of 'building', 'ready', or 'error'
        TODO: docstr
    """
    response = {}
    response['manifest'] = args.manifest
    response['status'] = status
    response['message'] = message
    write_to_file(args.status_file, json.dumps(response, indent=4))

#=============================================================================
# ESP == EFI System Partition, where EFI wants to scan for FS0:.


def create_ESP(args, blockdev, vmlinuz_gzip, cpio_gzip):
    # tftp_dir has "images/nodeZZ" tacked onto it from caller.
    # Grub itself is pulled live from L4TM repo at setup networking time.
    grub = '/'.join(args.tftp_dir.split('/')[:-2]) + '/grub/grubnetaa64.efi'

    ESP_mnt = '%s/ESP' % (args.build_dir)   # VFAT FS
    os.makedirs(ESP_mnt, exist_ok=True)     # That was easy

    undo_mount = False
    try:
        # This happens on containers, not sure why...
        assert os.path.exists(blockdev), 'Cannot find mapper file %s' %s

        cmd = 'mkfs.vfat ' + blockdev
        ret, stdout, stderr = piper(cmd)
        assert not ret, cmd

        # Step 3: Make, mount and fill out the file system.  Put everything
        # under /grub.  grubnetaa64.efi turns around and grabs /grub/grub.cfg.
        # EFI directory separator is backslash, while grub is forward.

        cmd = 'mount %s %s' % (blockdev, ESP_mnt)
        ret, stdout, stderr = piper(cmd)
        assert not ret, cmd
        undo_mount = True

        with open(ESP_mnt + '/startup.nsh', 'w') as f:
            f.write('\\grub\\grubnetaa64.efi\n')
        grubdir = ESP_mnt + '/grub'
        print('SDHC GRUB DIR AT %s' % grubdir)
        os.makedirs(grubdir)
        shutil.copy(vmlinuz_gzip, grubdir)
        shutil.copy(cpio_gzip, grubdir)

        shutil.copy(grub, grubdir)

        with open(grubdir + '/grub.cfg', 'w') as f:
            f.write('linux /grub/%s\n' % os.path.basename(vmlinuz_gzip))
            f.write('initrd /grub/%s\n' % os.path.basename(cpio_gzip))
            f.write('boot\n')

    except Exception as e:
        pass    # Just keep it here

    if undo_mount:
        cmd = 'umount ' + ESP_mnt
        ret, stdout, stderr = piper(cmd)
        assert not ret, cmd

    return undo_mount   # suppress final copy if this didn't work

#=============================================================================
# SNBU == Single Node Bringup, the first turnon of node boards.
# It will get burned onto SDHC/USB for single node bringup (SNBU).
# This will be pulled over HTTP, dd'd, etc.  Keep it small but useful.
# Most cpio.gz are under 200M, vmlinuz.gz under 7M, so this leaves
# at least 50M of space for copying log files, etc.  SNBU shouldn't
# make all that much data, he says with a smile.


def create_SNBU_image(args, vmlinuz_gzip, cpio_gzip):
    update_status(args, 'Building SNBU SDHC image')
    ESP_img = '%s/%s.ESP' % (args.build_dir, args.hostname)
    ESP_target = '%s/%s' % (args.tftp_dir, ESP_img)     # node-specific by now
    if os.path.exists(ESP_target):                      # shutil.copy below
        os.unlink(ESP_target)

    # Step 1: create the image file, burn GPT and ESP on it.

    with open(ESP_img, 'wb') as f:
        os.posix_fallocate(f.fileno(), 0, 256 << 20)
    undo_kpartx = do_copy = False     # until I make it that far.

    try:    # piper catches many things, asserts get me out early
        cmd = 'parted -s ' + ESP_img    # Yes, -s goes right here
        cmd += ' mklabel gpt mkpart ESP fat32 1MiB 100% set 1 boot on'
        ret, stdout, stderr = piper(cmd)
        assert not ret, cmd

        # Step 2: located the partition and create a block device.
        # Ass-u-me enough loopback devics to go around.

        cmd = 'kpartx -av %s' % ESP_img
        ret, stdout, stderr = piper(cmd)
        assert not ret, cmd
        undo_kpartx = True
        time.sleep(1)
        for e in stdout.decode().split():    # "add map loopXXp1 ...."
            if e.startswith('loop') and e.endswith('p1'):
                blockdev = '/dev/mapper/' + e
                break
        else:
            raise RuntimeError('Cannot discern loopback device in %s' % stdout)

        # Step 3: fill it out

        do_copy = create_ESP(args, blockdev, vmlinuz_gzip, cpio_gzip)

    except AssertionError as e:
        print('%s failed: errno = %d: %s' % (str(e), ret, stderr))
    except RuntimeError as e:
        print('%s: errno = %d: %s' % (str(e), ret, stderr))
    except Exception as e:
        print('%s: errno = %d: %s' % (str(e), ret, stderr))

    if undo_kpartx:
        cmd = 'kpartx -d %s' % ESP_img
        ret, stdout, stderr = piper(cmd)
        assert not ret, cmd

    if do_copy:
        shutil.copy(ESP_img, args.tftp_dir)

#=============================================================================
# This is just as fast as gzip standalone program and gives better error
# handling.  500M cpio file takes about 20 seconds for reduction to 180M (both
# methods, gzip command defaults to level 6).
# TMAS PXE is about 100 MB / hour xfer then 500 seconds to uncompress 180M
#          or about two hours to boot
# FAME PXE is about   6 MB / sec  xfer then  15 seconds to uncompress 180M
#          or about one minute to boot
# REAL HW  is about xxx MB per hour; xxx seconds to uncompress 180M


def compress_bootfiles(args, vmlinuz_file, cpio_file):
    cpio_gzip = args.tftp_dir + '/' + os.path.basename(cpio_file) + '.gz'
    vmlinuz_gzip = args.tftp_dir + '/' + args.hostname + '.vmlinuz.gz'

    update_status(args, 'Compressing kernel')
    with open(vmlinuz_file, 'rb') as f_in:
        with gzip.open(vmlinuz_gzip, mode='wb', compresslevel=6) as f_out:
            shutil.copyfileobj(f_in, f_out)

    update_status(args, 'Compressing File System')
    with open(cpio_file, 'rb') as f_in:
        with gzip.open(cpio_gzip, mode='wb', compresslevel=6) as f_out:
            shutil.copyfileobj(f_in, f_out)

    return vmlinuz_gzip, cpio_gzip

#==============================================================================


def execute(args):
    """
        Customize Filesystem image: set hostname, cleanup sources.list,
    install packages, create .CPIO from customized FS, remove temporary
    untar folder.

    :param 'args': [object] argparse.Namespace from command-line parsing
    :return: [dict] response with 'status' and 'message' key.
        'status' = 200 means success.
        Not 200 - failure. 'message' - is a message string that briefly
            explains the error\success status.
    """
    global _verbose, _debug

    _verbose = args.verbose
    _debug = args.debug

    response = {  # No errors occured yet! Let's keep it this way.
        'status': 200,
        'message': 'System image was created.'
    }
    args.status_file = args.tftp_dir + '/status.json'

    # It's a big try block because individual exception handling
    # is done inside those functions that throw RuntimeError.
    try:
        update_status(args, 'Untar golden image')
        new_fs_dir = untar(args.build_dir, args.golden_tar)

        update_status(args, 'Configuration file updates')

        # Use hostname and client_id
        set_hosts(new_fs_dir, args.hostname)
        set_hostname(new_fs_dir, args.hostname)
        set_client_id(new_fs_dir, args.client_id)

        # Remove kernel/boot files.  This is superfluous as the find/cpio
        # ignores them.  The kernel gets copied to tftp_dir.
        vmlinuz_file = cleanout_kernel(args.build_dir, new_fs_dir)

        # This is the magic that preserves initrd as rootfs.
        fix_init(new_fs_dir)
        fix_rootfs(new_fs_dir)

        # Add packages and tasks from manifest.
        # Even if empty, it does an apt-get update/upgrade/dist-upgrade
        # in case golden image has gone stale.
        update_status(args, 'Installing ' + str(args.packages))
        cleanup_sources_list(new_fs_dir)
        install_packages(new_fs_dir, args.packages, args.tasks)

        # Create .cpio file from untar.  Filename done here in case
        # we ever want to pass it in as an option.
        update_status(args, 'Generating FS image')
        cpio_file = '%s/%s.cpio' % (args.build_dir, args.hostname)
        create_cpio(cpio_file, new_fs_dir)

        vmlinuz_gzip, cpio_gzip = compress_bootfiles(
            args, vmlinuz_file, cpio_file)
        create_SNBU_image(args, vmlinuz_gzip, cpio_gzip)

        # Free up space someday, but not during active development
        # remove_target(build_dir)

        update_status(args, 'PXE files ready to boot', 'ready')

    except RuntimeError as err:     # Caught earlier and re-thrown as this
        response['status'] = 505
        response['message'] = 'Filesystem image build failed: %s' % str(err)
    except Exception as err:        # Suppress Flask traceback
        response['status'] = 505
        response['message'] = 'Unexpected error: %d: %s' % (
            sys.exc_info()[2].tb_lineno, str(err))

    if response['status'] != 200:
        update_status(args, response['message'], 'error')

    return response


if __name__ == '__main__':
    """ Parse command line arguments and pass them to execute() function. """
    parser = argparse.ArgumentParser(
        description='Options to customize FS image.')

    # Default default value is "None"

    parser.add_argument('--hostname',
                        help='Hostname to use for the FS image')
    parser.add_argument('--client_id',
                        help='DHCP client ID in full machine coordinates."')
    parser.add_argument('--manifest',
                        help='Manifest namespace.')
    parser.add_argument('--golden_tar',
                        help='Location of pristine FS image tarball')
    parser.add_argument('--packages',
                        help='Extra packages to "apt-get install" on new FS.')
    parser.add_argument('--tasks',
                        help='Tasks to "tasksel install" on new FS.')
    parser.add_argument('--build_dir',
                        help='Scratch folder for building FS images.')
    parser.add_argument('--tftp_dir',
                        help='Absolute path to the dnsmasq TFTP folder.')
    parser.add_argument('-v', '--verbose',
                        help='Make it talk. Verbosity levels from 1 to 5',
                        action='store_true')
    parser.add_argument('--debug',
                        help='Matrix has you. Enter the debugging mode.',
                        action='store_true')
    args, _ = parser.parse_known_args()
    execute(args)

    raise SystemExit(0)
