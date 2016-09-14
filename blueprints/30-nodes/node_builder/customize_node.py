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
import gzip
import json
import os
import requests as HTTP_REQUESTS
import shutil   # explicit namespace differentiates from our custom FS routines
import sys
import tarfile
import time

from glob import glob
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

#=============================================================================
# MAGIC: turn a transient initrd into a persistent rootfs with two corrective
# actions on the golden image:
# 1. Set correct symbolic link to a chrooted /init to /sbin/init
# 2. Remove the UUID-based mount in /etc/fstab that fails.  Actually,
#    just rewrite the whole thing.


def persist_initrd(args):
    """

    :param 'args.new_fs_dir': [str] where to find the fs being customized
    :return: 'None' on success. Raise 'RuntimeError' on problems.
    """
    update_status(args, 'Make initrd persistent as rootfs')
    try:
        with workdir(args.new_fs_dir):  # At the root
            if os.path.exists('init'):  # no leading slash!!!
                os.unlink('init')
            make_symlink('sbin/init', 'init')
            with open('etc/fstab', 'w') as f:   # no leading slash!!!
                f.write('proc /proc proc defaults 0 0\n')
    except RuntimeError as err:         # Expecting this from make_symlink...
        raise RuntimeError(str(err))    # ...so let it print the err message
    except Exception as err:
        raise RuntimeError('persist_initrd() failed: %s' % str(err))

#==============================================================================


def cleanup_sources_list(args):
    """
        Golden image from (vm)debootstrap leave two pieces of useless info:
    1. sources.list refers to us.debian.org
    2. source.list.d/base.list is copied from the running host.
    Neither helps, both are wrong, blow it away.

    :param 'args.new_fs_dir': [str] path to the file system being customized.
    :return: 'None' on success. Raise 'RuntimeError' on problems.
    """
    update_status(args, 'Set /etc/apt/sources*')
    sources_list = '%s/etc/apt/sources.list' % args.new_fs_dir
    sources_base = '%s.d/base.list' % sources_list

    try:
        remove_target(sources_base)

        content = [
            '# Created by TMMS for %s on %s' % (args.hostname, time.ctime()),
            '# a.k.a. %s' % args.node_coord,
            'deb %s %s %s' % (
                args.repo_mirror, args.repo_release, ' '.join(args.repo_areas))
        ]
        write_to_file(sources_list, '\n'.join(content))
    except RuntimeError as err:
        raise RuntimeError('clean_sources_list() failed: %s' % str(err))

#==============================================================================


def set_client_id(args):
    """
        Augment dhclient configuration file

    :param 'new_fs_dir': [str] path to the file system location to customize.
    :param 'node_coord': [str] full machine coordinate used as client ID.
    :return: 'None' on success. Raise 'RuntimeError' on problems.
    """
    update_status(args, 'Set ClientID for dhcpc')
    dhclient_conf = '%s/etc/dhcp/dhclient.conf' % args.new_fs_dir
    try:
        with open(dhclient_conf, 'a') as f:
            f.write('\nsend dhcp-client-identifier "%s";\n' % args.node_coord)
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
    fname = '%s/etc/environment' % args.new_fs_dir
    try:
        if os.path.exists(fname):
            remove_target(fname)

        proxy = getattr(args, 'web_proxy', 'web-proxy.corp.hpecorp.net:8080')
        no_proxy = '10.0.0.0/8'     # FIXME: calculate something for real HW
        content = [
            'http_proxy=http://%s' % proxy,
            'https_proxy=https://%s' % proxy,
            'no_proxy=127.0.0.0/8,%s' % no_proxy
        ]
        content = '\n'.join(content)
        write_to_file(fname, content)
    except RuntimeError as err:
        raise RuntimeError('Cannot set %s: %s' % (fname, str(err)))


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
    fname = '%s/etc/hosts' % args.new_fs_dir
    try:
        if os.path.exists(fname):
            remove_target(fname)

        content = [
            '127.0.0.1   localhost',
            '127.1.0.1   %s' % args.hostname
        ]
        content = '\n'.join(content)

        write_to_file(fname, content)
    except RuntimeError as err:
        raise RuntimeError('Cannot set %s: %s' % (fname, str(err)))


def set_l4tm_sudo(args):
    """
        Set sudoer policy of no password for user l4tm.  That user was
    configured with sudo in the golden image via vmdebootstrap.  This
    removes the password restriction for easier automation and has been
    approved by Operational Security.  See also set_l4tm_pubkey().

    :param 'new_fs_dir': [str] path to the file system location to customize.
    :return: 'None' on success. Raise 'RuntimeError' on problems.
    """
    update_status(args, 'Create /etc/sudoers.d/l4tm')
    fname = '%s/etc/sudoers.d/l4tm' % args.new_fs_dir
    try:
        if os.path.exists(fname):
            remove_target(fname)

        content = [                             # Speed up subsequent sudos
            'l4tm\t ALL = NOPASSWD: ALL',       # No passwd
            'Defaults timestamp_timeout=120',   # Don't ask again for 2 hours..
            'Defaults !tty_tickets',            # On any terminal
        ]
        write_to_file(fname, '\n'.join(content))
    except RuntimeError as err:
        raise RuntimeError('Cannot set %s: %s' % (fname, str(err)))

#==============================================================================


def set_l4tm_pubkey(args):
    """
        Add the l4tm_pubkey data to /home/l4tm/.ssh/authorized_keys.
    Where it comes from is your problem, but ssh-key -t rsa is a good start.

    :param 'l4tm_pubkey': [str] RSA public key
    :return: 'None' on success. Raise 'RuntimeError' on problems.
    """
    update_status(args, 'Set authorized keys file for user l4tm')
    if args.l4tm_pubkey is None:
        return
    with workdir(args.new_fs_dir):
        with open('etc/passwd', 'r') as f:
            for line in f:
                if line.startswith('l4tm:'):
                    _, _, uid, gid, gecos, home, shell = line.split(':')
                    uid = int(uid)
                    gid = int(gid)
                    dotssh = home[1:] + '/.ssh'     # relative to workdir
                    auth = dotssh + '/authorized_keys'
                    break
            else:
                raise RuntimeError('Cannot find user l4tm')
        os.makedirs(dotssh, mode=0o700, exist_ok=True)
        with open(auth, 'w+') as f:
            f.write('\n')
            f.write(args.l4tm_pubkey)
        os.chmod(auth, 0o600)
        os.chown(auth, uid, gid)
        os.chown(dotssh, uid, gid)

#==============================================================================


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
# Automatically answering yes is harder than it looks.
# --assume-yes and -y might not be forceful enough to overwrite a confg file.
# --force-yes is TOO forceful in some occasions, although probably not here.
#  http://superuser.com/questions/164553/automatically-answer-yes-when-using-apt-get-install
# and
# http://www.microhowto.info/howto/perform_an_unattended_installation_of_a_debian_package.html
# have the best answers.
# export DEBIAN_FRONTEND=noninteractive
# apt-get update -q
# apt-get install -q -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold"


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
    :return [boolean] True if it worked, False otherwise with updated status.
    """
    # Separate the space-delimited list of packages into URLs and package names
    if args.packages is None:
        downloads = None
        packages = None
        msg = 'Updating/upgrading packages from golden image'
    else:
        pkglist = args.packages.split(' ')
        downloads = [p for p in pkglist if
            (p.startswith('http://') or p.startswith('https://'))]
        packages = [p for p in pkglist if p not in downloads]
        msg = 'Installing %d packages and %d URL downloads' % (
            len(packages), len(downloads))
    update_status(args, msg)

    # Fill out the install script.  Everything goes at root $HOME.
    installsh = '/root/install.sh'
    installog = '/root/install.log'
    script_file = args.new_fs_dir + installsh
    script_header = """#!/bin/bash
# Created %s
set -ue
cd /root
exec > %s 2>&1
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get upgrade -q --assume-yes
apt-get dist-upgrade -q --assume-yes
""" % (time.ctime(), installog)

    with open(script_file, 'w') as install:
        install.write(script_header)

        install.write('\n# Packages: %s\n' % packages)
        if packages is not None:
            for pkg in packages:
                cmd = 'apt-get install -q -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" %s\n' % pkg
                install.write(cmd)

            # FIXME: zero out the apt cache, save some space?

        install.write('\n# Tasks: %s\n' % args.tasks)
        if args.tasks is not None:
            for task in args.tasks.split(','):
                cmd = 'tasksel install %s\n' % task
                install.write(cmd)

        install.write('\n# Show me the Debians! (%d)\n' % len(downloads))
        for pkg in downloads:
            deb = pkg.split('/')[-1]
            install.write('# %s\n' % pkg)
            pkgresp = HTTP_REQUESTS.get(pkg, verify=False)
            if pkgresp.status_code != 200:
                msg = 'Status %d: could not download "%s"' % (
                    pkgresp.status_code, pkg)
                args.logger.error(msg)
                install.write('# %s\n\n' % msg)
                continue
            with open(args.new_fs_dir + '/root/' + deb, 'wb') as debian:
                debian.write(pkgresp.content)
            install.write('dpkg -i %s\n# rm %s\n\n' % (deb, deb))

    os.chmod(script_file, 0o744)

    try:
        cmd = '/usr/sbin/chroot %s %s ' % (args.new_fs_dir, installsh)
        # This can take MINUTES.  "album" pulls in about 80 dependent packages.
        # While running, sys_image/root/install.log is updated.  That could be
        # tailed and status updated, MFT' time.
        ret, stdout, stderr = piper(cmd, use_call=True)
        assert not ret, 'chroot failed: errno %d' % (ret)
        return True
    except Exception as err:
        args.logger.error('%s: %s' % (str(err), stderr))
        with open(args.new_fs_dir + installog, 'r') as log:
            args.logger.debug(log.read())
        raise RuntimeError('Couldn\'t install packages: %s' % str(err))
    return False

#==============================================================================


def update_status(args, message, status='building'):
    """
        Update status of the node at the given state in its tftp/images/nodeX
    directory.
        Status must be one of 'building', 'ready', or 'error'
    """
    if getattr(args, 'dryrun', False):
        return
    args.logger(message)
    response = {}
    response['manifest'] = args.manifest.namespace
    response['status'] = status
    response['message'] = message
    response['coordinate'] = args.node_coord    # Troubleshooting and QA
    response['node_id'] = args.node_id
    # Rally DE118: make it an atomic update
    newstatus = args.status_file + '.new'
    write_to_file(newstatus, json.dumps(response, indent=4))
    os.replace(newstatus, args.status_file)

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

    whitney_FW_image = True     # FW updates for Whitney need 128M hole
    if whitney_FW_image:
        img_size = 384 << 20
        ESP_offset = 129
    else:
        img_size = 256 << 20    # Downloads and boots much faster
        ESP_offset = 1

    with open(ESP_img, 'wb') as f:
        os.posix_fallocate(f.fileno(), 0, img_size)
    undo_kpartx = do_copy = False     # until I make it that far.

    try:    # piper catches many things, asserts get me out early
        cmd = 'parted -s %s ' % ESP_img    # Yes, -s goes right here
        cmd += 'mklabel gpt '
        cmd += 'unit MiB mkpart primary fat32 %d 100%% ' % ESP_offset
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
        args.logger.error('%s failed: errno = %d: %s' % (str(e), ret, stderr))
    except RuntimeError as e:
        args.logger.error('%s: errno = %d: %s' % (str(e), ret, stderr))
    except Exception as e:
        args.logger.critical('%s: errno = %d: %s' % (str(e), ret, stderr))

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
    # You can't call this twice
    # logging.basicConfig(filename=args.build_dir + '/build.log',
    #   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    #   level=logging.INFO)

    if args.debug:
        args.verbose = True
    else:
        # Ass-u-me this is the first child in a fork-setsid-fork daemon chain
        try:
            os.chdir('/tmp')
            os.setsid()
            forked = os.fork()
            args.logger.debug('Spawning parent PID=%s' % (forked))
            # Release the wait that should be done by original parent
            if forked > 0:
                args.logger.debug('Closing parent PID=%s.' % (forked))
                os._exit(0)  # RTFM: this is the preferred exit after fork()
            update_status(args,
                          'Rocky\'s rookie spawned a rookie %s...' % forked)
        except OSError as err:
            args.logger.debug('Faild to spawn a child: %s ' % err)
            raise RuntimeError(
                'Rocky\'s rookie\'s rookie is down! Bad Luck. [%s]' % str(err))

    response = {  # No errors occured yet! Let's keep it this way.
        'status': 200,
        'message': 'System image was created.'
    }

    args.logger(' --- Starting node image build ---')

    # It's a big try block because individual exception handling
    # is done inside those functions that throw RuntimeError.
    # When some of them fail they'll handle last update_status themselves.
    try:
        update_status(args, 'Untar golden image')
        args.new_fs_dir = untar(args.build_dir, args.golden_tar)
        tmp = extract_bootfiles(args)
        assert len(tmp) == 1, 'Golden image %s had no kernel' % args.golden_tar
        vmlinuz_golden = tmp[0]
        update_status(args, 'Found golden kernel %s' %
                      os.path.basename(vmlinuz_golden))

        # Global and account config files
        set_environment(args)
        set_hostname(args)
        set_hosts(args)
        set_client_id(args)
        set_l4tm_sudo(args)
        set_l4tm_pubkey(args)

        persist_initrd(args)

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
        args.logger.error('Failed to customize image! RuntimeError: %s' % err)
        response['status'] = 505
        response['message'] = 'Filesystem image build failed: %s' % str(err)
    except Exception as err:        # Suppress Flask traceback
        args.logger.error('Failed to customize image! Exception: %s' % err)
        response['status'] = 505
        response['message'] = 'Unexpected error: %d: %s' % (
            sys.exc_info()[2].tb_lineno, str(err))

    if response['status'] != 200:
        update_status(args, response['message'], 'error')

    args.logger('finished: %s' % (response))
    if not args.debug:  # I am the grandhild; release the wait() by init()
        args.logger.debug('Closing the build child.')
        os._exit(0)     # RTFM: this is the preferred exit after fork()

    return response


if __name__ == '__main__':
    """ Parse command line arguments and pass them to execute() function. """
    parser = argparse.ArgumentParser(
        description='Options to customize FS image.')

    # Default default value is "None"

    parser.add_argument('--hostname',
                        help='Hostname to use for the FS image')
    parser.add_argument('--node_coord',
                        help='Full machine coordinate of this node."')
    parser.add_argument('--node_id',
                        help='Node number (1-40)."')
    parser.add_argument('--manifest',
                        help='Manifest namespace.')
    parser.add_argument('--golden_tar',
                        help='Location of pristine FS image tarball')
    parser.add_argument('--repo_mirror',
                        help='URL of L4TM mirror')
    parser.add_argument('--repo_release',
                        help='release to use on mirror')
    parser.add_argument('--repo_areas',
                        help='areas to use from a release on mirror')
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
