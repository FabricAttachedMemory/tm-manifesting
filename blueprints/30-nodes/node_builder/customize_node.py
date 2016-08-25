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

#==============================================================================


def extract_bootfiles(args):
    """
        Remove boot/vmlinuz* and boot/initrd.img/ files from new file system.
    These files are not needed in the rootfs for diskless boot.  Move them
    to args.build_dir for future use.  Return any kernel(s) that are found.
    Let the caller decide if the count is an error.

    :param 'args.build_dir': [str] where to move the unecessary files.
    :param 'args.new_fs_dir': [str] where to find the unecessary files.
    :return: 'None' on success. Raise 'RuntimeError' on problems.
    """
    update_status(args, 'Extract any /boot/[vmlinuz,initrd]')
    boot_dir = '%s/boot/' % args.new_fs_dir
    vmlinuz = glob('%s/vmlinuz*' % (boot_dir))      # one list
    initrd = glob('%s/initrd.img*' % (boot_dir))    # two lists
    vmlinuzes = []
    try:
        for source in vmlinuz + initrd:            # move them all
            copy_into = '%s/%s' % (args.build_dir, os.path.basename(source))
            copy_target_into(source, copy_into)
            if '/vmlinuz' in copy_into:
                vmlinuzes.append(copy_into)
            remove_target(source)
        return vmlinuzes
    except Exception as err:
        raise RuntimeError('extract_bootfiles() failed: %s' % str(err))


def fix_init(args):
    """
        Set correct symbolic link to a chrooted /init file from /sbin/init

    :param 'args.new_fs_dir': [str] where to find the fs being customized
    :return: 'None' on success. Raise 'RuntimeError' on problems.
    """
    update_status(args, 'Set /init')
    try:
        with workdir(args.new_fs_dir):  # At the root
            if os.path.exists('init'):  # no leading slash!!!
                os.unlink('init')
            make_symlink('sbin/init', 'init')
    except RuntimeError as err:         # Expecting this from make_symlink...
        raise RuntimeError(str(err))    # ...so let it print the err message
    except Exception as err:
        raise RuntimeError('fix_init() failed: %s' % str(err))

#=============================================================================
# setup_golden_image leaves a UUID-based mount in /etc/fstab that fails.
# Simplify life.


def fix_rootfs(args):
    """
        Create simpler /etc/fstab appropriate for rootfs.

    :param 'args.new_fs_dir': [str] where to find the fs being customized
    :return: 'None' on success. Raise 'RuntimeError' on problems.
    """
    update_status(args, 'Set /etc/fstab')
    try:
        with workdir(args.new_fs_dir):          # At the root
            with open('etc/fstab', 'w') as f:   # no leading slash!!!
                f.write('proc /proc proc defaults 0 0\n')
    except Exception as e:
        raise RuntimeError('fix_rootfs() failed: %s' % str(e))

#==============================================================================


def cleanup_sources_list(args):
    """
        Check if /etc/apt/source.list.d/base.list file exists. If so, move it
    into /etc/apt/sources.list, because base.list is causing collisions.

    :param 'args.new_fs_dir': [str] path to the file system being customized.
    :return: 'None' on success. Raise 'RuntimeError' on problems.
    """
    update_status(args, 'Set /etc/apt/sources*')
    sources_list = '%s/etc/apt/sources.list' % args.new_fs_dir
    sources_base = '%s/etc/apt/sources.list.d/base.list' % args.new_fs_dir

    if not os.path.exists(sources_base):
        update_status('/etc/apt/sources.list.d/ is empty, nothing to do.')
        return None

    sources_updated = set_sources_areas(
        sources_base, ['main', 'contrib', 'non-free'])

    try:
        remove_target(sources_base)
        remove_target(sources_list)
        write_to_file(sources_list, sources_updated)
    except RuntimeError as err:
        raise RuntimeError('clean_sources_list() failed: %s' % str(err))


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


def set_client_id(args):
    """
        Augment dhclient configuration file

    :param 'new_fs_dir': [str] path to the file system location to customize.
    :param 'client_id': [str] hostname to be used for given system image.
    :return: 'None' on success. Raise 'RuntimeError' on problems.
    """
    update_status(args, 'Set ClientID for dhcpc')
    dhclient_conf = '%s/etc/dhcp/dhclient.conf' % args.new_fs_dir
    try:
        with open(dhclient_conf, 'a') as f:
            f.write('\nsend dhcp-client-identifier "%s";\n' % args.client_id)
    except Exception as err:
        raise RuntimeError('Cannot set DHCP client ID: %s' % str(err))

#==============================================================================


def set_environment(args):
    """
        Set new /etc/environment http_proxy stuff on the file system image.

    :param 'new_fs_dir': [str] path to the file system location to customize.
    :return: 'None' on success. Raise 'RuntimeError' on problems.
    """
    update_status(args, 'Create /etc/environment')
    env_file = '%s/etc/environment' % args.new_fs_dir
    try:
        if os.path.exists(env_file):
            remove_target(env_file)

        proxy = getattr(args, 'web_proxy', 'web-proxy.corp.hpecorp.net:8080')
        no_proxy = '10.0.0.0/8'     # FIXME: calculate something for real HW
        content = [
            'http_proxy=http://%s' % proxy,
            'https_proxy=https://%s' % proxy,
            'no_proxy=127.0.0.0/8,%s' % no_proxy
        ]
        content = '\n'.join(content)
        write_to_file(env_file, content)
    except RuntimeError as err:
        raise RuntimeError('Cannot set /etc/environment: s' % str(err))


def set_hostname(args):
    """
        Set new /etc/hostname on the file system image.

    :param 'new_fs_dir': [str] path to the file system location to customize.
    :param 'hostname': [str] hostname to be used for given system image.
    :return: 'None' on success. Raise 'RuntimeError' on problems.
    """
    update_status(args, 'Create /etc/hostname')
    hostname_file = '%s/etc/hostname' % args.new_fs_dir
    try:
        if os.path.exists(hostname_file):
            remove_target(hostname_file)
        write_to_file(hostname_file, args.hostname)
    except RuntimeError as err:
        raise RuntimeError('Cannot set /etc/hostname: %s' % str(err))


def set_hosts(args):
    """
        Set new /etc/hosts on the file system image.

    :param 'new_fs_dir': [str] path to the file system location to customize.
    :param 'hostname': [str] hostname to be used for given system image.
    :return: 'None' on success. Raise 'RuntimeError' on problems.
    """
    update_status(args, 'Create /etc/hosts')
    hosts_file = '%s/etc/hosts' % args.new_fs_dir
    try:
        if os.path.exists(hosts_file):
            remove_target(hosts_file)

        content = []
        content.append('127.0.0.1   localhost')     # visual alignment
        content.append('127.1.0.1   %s' % args.hostname)
        content = '\n'.join(content)

        write_to_file(hosts_file, content)
    except RuntimeError as err:
        raise RuntimeError('Cannot set /etc/hosts: s' % str(err))


def create_cpio(args):
    """
        Get the non-boot pieces, ignoring initrd, kernel, and /boot.

    :param 'dest_file': [str] path to save cpio archive
    :param 'args.new_fs_dir': [str] folder to create .cpio from.
    :return: cpio_file
    """
    cpio_file = '%s/%s.cpio' % (args.build_dir, args.hostname)
    update_status(args, 'Create %s from %s' % (cpio_file, args.new_fs_dir))
    try:
        # Skip things even though they may have been moved
        found_data = find(
            args.new_fs_dir,
            ignore_files=['vmlinuz', 'initrd.img'],
            ignore_dirs=['boot'])

        cmd = 'cpio --create --format \'newc\''
        cpio_stdin = '\n'.join(found_data).encode()  # needed for Popen pipe.

        with open(cpio_file, 'w') as dest_obj:
            # create CPIO relative to the 'find' path, to avoid '/' in archive
            # names.  Note: searching outside of untar folder results in a
            # "full path" string (e.g. whatever/untar/boot...., instead
            # ./boot...). This causes Kernel Panic when trying to boot with
            # such a cpio file.
            with workdir(args.new_fs_dir):
                ret, cpio_out, cpio_err = piper(
                    cmd, stdin=cpio_stdin, stdout=dest_obj)
                assert not ret, 'cpio failed: %s' % cpio_err

        # output find data to a log file
        if args.verbose:
            with open('/tmp/man_find.log', 'w') as file_obj:
                file_obj.write('\n'.join(found_data))   # FIXME proper logging
        return cpio_file

    except Exception as err:
        raise RuntimeError('Couldn\'t create "%s" from "%s": %s' % (
            cpio_file, args.new_fs_dir, str(err)))


#==============================================================================


def install_packages(args):
    """
        Install list of packages into the filesystem image.
    Function will generate a bash script with lines of "apt-get install"
    in it.   This script is placed under the file system. Then, this function
    will execute this script under the chrooted to "args.new_fs_dir". Also,
    every action performed by generated install.sh script is logged into the
    'args.new_fs_dir + "/manifesting.log"' file.

    :param 'args.new_fs_dir': [str] path to filesystem image to customize.
    :param 'args.packages': [list] of packages 'apt-get install'.
    :param 'args.tasks': [list] of tasks for 'tasksel'.
    """
    msg = 'Installing ' + str(args.packages) if args.packages else \
        'Updating/upgrading base packages'
    update_status(args, msg)

    script_header = """#!/bin/bash
# Created %s
set -ue
exec > /install.log 2>&1  # /tmp/ is cleaned out of boot
apt-get update
apt-get upgrade --assume-yes
apt-get dist-upgrade --assume-yes
""" % time.ctime()
    script_file = args.new_fs_dir + '/install.sh'
    with open(script_file, 'w') as file_obj:
        file_obj.write(script_header)

        file_obj.write('\n# Packages: %s\n' % args.packages)
        if args.packages is not None:
            for pkg in args.packages.split(','):
                cmd = 'apt-get install --assume-yes %s\n' % pkg
                file_obj.write(cmd)

        file_obj.write('\n# Tasks: %s\n' % args.tasks)
        if args.tasks is not None:
            for task in args.tasks.split(','):
                cmd = 'tasksel install %s\n' % task
                file_obj.write(cmd)

    os.chmod(script_file, 0o744)

    try:
        cmd = '/usr/sbin/chroot %s %s ' % (args.new_fs_dir, '/install.sh')
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
    if args.verbose:    # sometimes it's for stdout, sometimes the file
        print(' - %s: %s' % (args.hostname, message))
    response = {}
    response['manifest'] = args.manifest.namespace
    response['status'] = status
    response['message'] = message
    write_to_file(args.status_file, json.dumps(response, indent=4))

#=============================================================================
# ESP == EFI System Partition, where EFI wants to scan for FS0:.


def create_ESP(args, blockdev, vmlinuz_gzip, cpio_gzip):
    update_status(args, 'Creating and filling ESP')

    # tftp_dir has "images/nodeZZ" tacked onto it from caller.
    # Grub itself is pulled live from L4TM repo at setup networking time.
    grub = '/'.join(args.tftp_dir.split('/')[:-2]) + '/grub/grubnetaa64.efi'

    ESP_mnt = '%s/mnt' % (args.build_dir)   # VFAT FS
    os.makedirs(ESP_mnt, exist_ok=True)     # That was easy

    undo_mount = False
    try:
        # This happens on containers, not sure why...
        assert os.path.exists(blockdev), \
            'Cannot find mapper file %s' % blockdev

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
        update_status(args, 'SDHC GRUB DIR AT %s' % grubdir)
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
        cmd = 'parted -s %s ' % ESP_img    # Yes, -s goes right here
        cmd += 'mklabel gpt '
        cmd += 'unit MiB mkpart primary fat32 1 100% '
        cmd += 'set 1 boot on set 1 esp on '
        cmd += 'name 1 %s ' % args.hostname
        ret, stdout, stderr = piper(cmd)
        assert not ret, cmd

        # Step 2: located the partition and create a block device.
        # Ass-u-me enough loopback devics to go around.

        cmd = 'kpartx -asv %s' % ESP_img
        ret, stdout, stderr = piper(cmd)
        assert not ret, cmd
        undo_kpartx = True
        stdout = stdout.decode()
        assert stdout.startswith('add map loop'), \
            'Unexpected kpartx output: %s' % stdout
        blockdev = '/dev/mapper/' + stdout.split()[2]
        assert blockdev.endswith('p1'), \
            'Unexpected kpartx partition: %s' % blockdev

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
# handling.  500M cpio file takes about 20 seconds for reduction to 180M.
# Use gzip command's default compression level (6).  For 180M (base) FS:
# TMAS PXE is about 100 MB / hour xfer then 500 seconds to uncompress
#          so about two hours to boot
# FAME PXE is about   6 MB / sec  xfer then  30 seconds to uncompress
#          so about one minute to boot
# MFT/FRD  is about  xx MB / sec  xfer then  xx seconds to uncompress
#          so about  xx seconds to boot


def compress_bootfiles(args, vmlinuz_file, cpio_file):
    update_status(args, 'Compressing kernel and file system')

    vmlinuz_gzip = args.tftp_dir + '/' + args.hostname + '.vmlinuz.gz'
    with open(vmlinuz_file, 'rb') as f_in:
        with gzip.open(vmlinuz_gzip, mode='wb', compresslevel=6) as f_out:
            shutil.copyfileobj(f_in, f_out)

    cpio_gzip = args.tftp_dir + '/' + os.path.basename(cpio_file) + '.gz'
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
    if args.debug:
        args.verbose = True
    else:
        # Ass-u-me this is the first child in a fork-setsid-fork daemon chain
        try:
            os.chdir('/tmp')
            os.setsid()
            forked = os.fork()
            # Release the wait that should be done by original parent
            if forked > 0:
                os._exit(0)  # RTFM: this is the preferred exit after fork()
            update_status(args,
                          'Rocky\'s rookie spawned a rookie %s...' % forked)
        except OSError as err:
            raise RuntimeError(
                'Rocky\'s rookie\'s rookie is down! Bad Luck. [%s]' % str(err))

    response = {  # No errors occured yet! Let's keep it this way.
        'status': 200,
        'message': 'System image was created.'
    }

    # It's a big try block because individual exception handling
    # is done inside those functions that throw RuntimeError.
    try:
        update_status(args, 'Untar golden image')
        args.new_fs_dir = untar(args.build_dir, args.golden_tar)
        tmp = extract_bootfiles(args)
        assert len(tmp) == 1, 'Golden image %s had no kernel' % args.golden_tar
        vmlinuz_golden = tmp[0]
        update_status('Found golden kernel %s' %
                       os.path.basename(vmlinuz_golden))

        # Global config files
        set_environment(args)
        set_hostname(args)
        set_hosts(args)
        set_client_id(args)

        # MAGIC: turn a transient initrd into a persistent rootfs.
        fix_init(args)
        fix_rootfs(args)

        # FINALLY! Add packages and tasks from manifest.
        cleanup_sources_list(args)
        install_packages(args)

        # Was there a custom kernel?
        tmp = extract_bootfiles(args)
        if tmp:
            assert len(tmp) < 2, 'Too many custom kernels'
            update_status(args, 'Replacing golden kernel %s with %s' % (
                os.path.basename(vmlinuz_golden), os.path.basename(tmp[0])))
            vmlinuz_golden = tmp[0]

        cpio_file = create_cpio(args)

        vmlinuz_gzip, cpio_gzip = compress_bootfiles(
            args, vmlinuz_golden, cpio_file)
        create_SNBU_image(args, vmlinuz_gzip, cpio_gzip)

        # Free up space someday, but not during active development
        # remove_target(args.build_dir)

        update_status(args, 'PXE files ready to boot', 'ready')

        # Leave a copy of the controlling manifest for post-mortems
        manifest_tftp_file = args.manifest.namespace.replace('/', '.')
        copy_target_into(args.manifest.fullpath,
                         args.tftp_dir + '/' + manifest_tftp_file)

    except RuntimeError as err:     # Caught earlier and re-thrown as this
        response['status'] = 505
        response['message'] = 'Filesystem image build failed: %s' % str(err)
    except Exception as err:        # Suppress Flask traceback
        response['status'] = 505
        response['message'] = 'Unexpected error: %d: %s' % (
            sys.exc_info()[2].tb_lineno, str(err))

    if response['status'] != 200:
        update_status(args, response['message'], 'error')

    if not args.debug:  # I am the grandhild; release the wait() by init()
        os._exit(0)     # RTFM: this is the preferred exit after fork()

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
    args, _ = parser.parse_known_args()

    args.debug = True  # suppress daemonization
    execute(args)

    raise SystemExit(0)
