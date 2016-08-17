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
from contextlib import contextmanager
from glob import glob
import gzip
import json
import os
import tarfile
import shlex
import shutil   # explicit namespace differentiates from our custom FS routines
import sys

from subprocess import Popen, PIPE, CalledProcessError
import subprocess
from pdb import set_trace

from tmms.utils.utils import make_symlink

_verbose = None     # Poor man's class
_debug = None

#===============================================================================

@contextmanager
def workdir(path):
    """
        Change script's work directory to perform a set of operation.
    Set original directory back when done.
    """
    try:
        orig_dir = os.getcwd()
        os.chdir(path)
        yield
    except OSError as e:
        raise RuntimeError('os.chdir(%s) failed: %s' % (path, str(e)))
    finally:
        os.chdir(orig_dir)


def _fs_sanity_check(target):
    """
        Some file routines are HORRIBLY dangerous to run as root.
    Perform a few idiot checks.
    :param 'target': [str] path about to be copied/moved/overwritten/removed
    :return: 'None' on success. Raise 'AssertionError' on problems.
    """
    if os.geteuid():    # Not root?  Trust the FS
        return
    target = target.strip()
    assert target[0] == '/', 'Not an absolute path'
    elems = target.split('/')[1:]   # zeroth is empty string
    assert len(elems) > 2, 'Target is a primary directory'
    assert elems[:2] == ['var', 'lib'], 'Target is not under /var/lib'


def copy_target_into(target, into):
    """
        Wrapper around shutil.copy* functions. Main intention is to catch a
    specific exception and raise RuntimeError with a meaningful message. Also
    provides debugging and verbose options.

    :param 'target': [str] path to an object that needs to be copied.
    :param 'into': [str] path to the destination object (dir path or filename)
    :return: 'None' on success. Raise 'RuntimeError' on problems.
    """
    try:
        if _verbose:
            print(' - Copying "%s" into "%s"...' % (target, into))
        _fs_sanity_check(target)
        if os.path.isdir(target):
            shutil.copytree(target, into) # copy directory
        else:
            shutil.copyfile(target, into) # copy single file
    except (AssertionError, RuntimeError, EnvironmentError) as err:
        raise RuntimeError ('Couldn\'t copy "%s" into "%s": %s' %
            (target, into, str(err)))


def remove_target(target):
    """
        Remove "target" file.

    :param 'target': [str] path to the file to remove.
    :return: 'None' on success. Raise 'RuntimeError' on problems.
    """
    try:
        if _verbose:
            print(' - Removing "%s"...' % (target))
        _fs_sanity_check(target)
        if os.path.isdir(target):
            shutil.rmtree(target)
        elif os.path.exists(target):
            os.remove(target)
    except (AssertionError, EnvironmentError) as e:
        raise RuntimeError ('Couldn\'t remove "%s": %s' % (target, str(e)))


def write_to_file(target, content):
    """
        Overwrite file in the targeted location with a new content.

    :param 'target': [str] path to a file to create or overwrite with a new content
    :param 'content': [str] content to use in the new\overwritten file.
    """
    try:
        _fs_sanity_check(target)
        with open(target, 'w+') as file_obj:
            if _verbose:
                print ('Writing into "%s": \n[\n%s\n]\n' % (target, content))
            file_content = '%s\n' % str(content)
            file_obj.write(file_content)
    except Exception as e:
        raise RuntimeError ('Write "%s" failed: %s' % (target, str(e)))


def slice_path(target, slice_ratio=2):
    """
        Slice long path string on half (or by slice_ratio amount). Sometimes
        there is no need to print an absolute path to a string where the
        first N directories are irrelavent to the user.

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

#===============================================================================


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
            copy_target_into(source, '%s/%s' % (target_dir, copy_into) )
            remove_target(source)
        # I want to return the kernel I found and moved.   In an error
        # condition (such as one of the unit tests) it may not be there.
        vmlinuz =  glob('%s/vmlinuz*' % (target_dir))
        return vmlinuz[0] if vmlinuz else None
    except Exception as err:
        raise RuntimeError ('Errror occured cleanout_kernel(): %s' % str(err))


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
    except Exception as err:
        raise RuntimeError('Error occured while fixing /init: %s' % str(err))

#===============================================================================
# setup_golden_image leaves a UUID-based mount that fails.  Also, FIXME
# rootfs needs some kind of TLC to show up in df.

def fix_rootfs(sys_img):
    try:
        with workdir(sys_img):      # At the root
            with open('etc/fstab', 'w') as f:    # no leading slash!!!
                f.write('proc /proc proc defaults 0 0\n')
    except Exception as e:
        raise RuntimeError('Error occured while fixing rootfs: %s' % str(e))

#===============================================================================


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
            print ('/etc/apt/sources.list.d/ is clean. Nothing to do here...')
        return None

    sources_updated = set_sources_areas(sources_base, ['main', 'contrib', 'non-free'])

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

#===============================================================================

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

#===============================================================================


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


def untar(destination, source):
    """
        Untar source file into destination folder. tar.tarfile.extractall
    will create all necessary (sub)directories.
    Note: When untaring into the existing folder to overwrite files,
    tarfile.extractall function will throw a FileExistsError
    if it can not overwrite broken symlinks of the tar'ed file.
    Nuke it from orbit, it's the only way to be sure.

    :param 'destination': [str] path to where to extract target into.
    :param 'source': [str] path to a .tar file to untar.
    :return: [str] path to untared content.  Raise RuntimeError on problems.
    """

    try:
        destination = destination + '/untar'
        remove_target(destination)  # succeeds even if missing
        if _verbose:
            print(' - Extracting "%s" into "%s"...' % (source, destination))
        with tarfile.open(source) as tar_obj:
            tar_obj.extractall(path=destination)
        return destination
    except (AssertionError, tarfile.ReadError, tarfile.ExtractError) as err:
        raise RuntimeError ('Error occured while untaring "%s": %s' %
            (source, str(err)))


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
        cmd = shlex.split(cmd)
        cpio_stdin = '\n'.join(found_data).encode() # needed for Popen pipe.

        with open(dest_file, 'w') as dest_obj:
            # create CPIO relative to the 'find' path, to avoid '/' in archive
            # names.  Note: searching outside of  untar folder results in a
            # "full path" string (e.g. whatever/untar/boot...., instead
            # ./boot...). This causes Kernel Panic when trying to boot with
            # such a cpio file.
            with workdir(src_dir):
                cpio = Popen(cmd, stdin=PIPE, stdout=dest_obj)
                cpio_out, cpio_err = cpio.communicate(input=cpio_stdin)

        # output find data to a log file
        if _verbose:
            with open('/tmp/man_find.log', 'w') as file_obj:
                file_obj.write('\n'.join(found_data))   # FIXME proper log

    except CalledProcessError as err:
        raise RuntimeError('Couldn\'t create "%s" from "%s": %s' %
            (dest_file, src_dir, str(e)))


def find(start_path, ignore_files=[], ignore_dirs=[]):
    """
        Emulating output of unix "find" command. Thus, have to build a list of all
    the directories and filenames using os.walk relative to the start of its walking
    directory.
    Note: os.walk expands its data into three variables, where 'dirs' and 'files'
    are not relative path, but  rather "basenames". Combining all together will
    result in a full path string. e.g:
            root + "/" dirs[0] + "/" + files[0] = /root/elemenOfDirs/elementOfFIles

    :param 'start_path': [str] path to start walk from.
    :param 'ignore_files': [list] filenames to ignore during the walk.
    :param 'ignore_dirs': [list] directories to ignore from walking through.
    :return: [list] all the walked directories and filenames  relative to the 'start_path'.
            This will save EACH directory relative path e,g: /path/to/top/ will 
            be saved as /path/, /path/to/ and /path/to/top/
    """
    result = []
    with workdir(start_path):       # so that can walk relative to untar'ed FS folder.
        for root, dirs, files in os.walk('.'):
            for dirname in dirs:        # each directory relative path to the root
                if dirname in ignore_dirs:
                    continue
                result.append(os.path.join(root, dirname))
            for filename in files:      # each filename relative path to the root
                if filename in ignore_files:
                    continue
                result.append(os.path.join(root, filename))
    return result

#===============================================================================


def install_packages(sys_img, pkg_list):
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
set -ue
exec > /install.log 2>&1  # /tmp/ is cleaned out of boot
apt-get update
apt-get upgrade --assume-yes
apt-get dist-upgrade --assume-yes
"""
    script_file = sys_img + '/install.sh'
    with open(script_file, 'w') as file_obj:
        file_obj.write(script_header)
        file_obj.write('\n')
        if pkg_list is not None:
            for pkg in pkg_list.split(','):
                cmd = 'apt-get install --assume-yes %s\n' % pkg
                file_obj.write(cmd)

    os.chmod(script_file, 0o744)

    try:
        cmd = '/usr/sbin/chroot %s %s ' % (sys_img, '/install.sh')
        cmd = shlex.split(cmd)
        # This can take MINUTES.  "album" pulls in about 80 dependent packages.
        # While running, sys_image/install.log is updated.  That could be
        # tail followed and status updated, MFT' time.
        subprocess.call(cmd)
    except Exception as err:
        raise RuntimeError('Couldn\'t install packages: %s' % str(err))

#===============================================================================


def update_status(destination, manifest, message, status='building'):
    """
        status must be one of 'building', 'ready', or 'error'
        TODO: docstr
    """
    response = {}
    response['manifest'] = manifest
    response['status'] = status
    response['message'] = message
    write_to_file(destination, json.dumps(response, indent=4))

#===============================================================================


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
    status_file = args.tftp_dir + '/status.json'

    # It's a big try block because individual exception handling
    # is done inside those functions that throw RuntimeError.
    try:
        update_status(status_file, args.manifest, 'Untar golden image')
        new_fs_dir = untar(args.build_dir, args.golden_tar)

        update_status(status_file, args.manifest, 'Configuration file updates')

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

        # Add packages and tasks from manifest.  FIXME: what about tasks?
        # Even if empty, it does an apt-get update/upgrade/dist-upgrade
        # in case golden image has gone stale.
        update_status(
            status_file, args.manifest, 'Installing ' + str(args.packages))
        cleanup_sources_list(new_fs_dir)
        install_packages(new_fs_dir, args.packages)

        # Create .cpio file from untar.  Filename done here in case
        # we ever want to pass it in as an option.
        update_status(status_file, args.manifest, 'Generating FS image')
        cpio_file = '%s/%s.cpio' % (args.build_dir, args.hostname)
        create_cpio(cpio_file, new_fs_dir)

        # This is just as fast as gzip standalone program and gives better
        # error handling.  500M cpio file takes about 20 seconds for
        # reduction to 180M (both methods, gzip command defaults to level 6).
        # Net results:
        # TMAS PXE is about 100M per hour; 500 seconds to uncompress 180M
        # FAME PXE is about xxxM per hour; xxx seconds to uncompress 180M
        # REAL HW  is about xxxM per hour; xxx seconds to uncompress 180M

        cpio_gzip = args.tftp_dir + '/' + os.path.basename(cpio_file) + '.gz'
        vmlinuz_gzip = args.tftp_dir + '/' + args.hostname + '.vmlinuz.gz'

        update_status(status_file, args.manifest, 'Compressing kernel')
        with open(vmlinuz_file, 'rb') as f_in:
            with gzip.open(vmlinuz_gzip, mode='wb', compresslevel=6) as f_out:
                shutil.copyfileobj(f_in, f_out)

        update_status(status_file, args.manifest, 'Compressing File System')
        with open(cpio_file, 'rb') as f_in:
            with gzip.open(cpio_gzip, mode='wb', compresslevel=6) as f_out:
                shutil.copyfileobj(f_in, f_out)

        # Free up space someday, but not during active development
        # remove_target(build_dir)

        update_status(
            status_file, args.manifest, 'PXE files ready to boot', 'ready')

    except RuntimeError as err:     # Caught earlier and re-thrown as this
         response['status'] = 505
         response['message'] = 'Filesystem image build failed: %s' % str(err)
    except Exception as err:        # Suppress Flask traceback
        response['status'] = 505
        response['message'] = 'Aye! Unexpected Server error: %s' % str(err)

    if response['status'] != 200:
        update_status(status_file, args.manifest, response['message'], 'error')

    return response


if __name__ == '__main__':
    """ Parse commind line arguments and pass it directly into execute() function. """
    parser = argparse.ArgumentParser(description='Options to customize FS image.')

    # Default default value is "None"

    parser.add_argument('--hostname',
        help='Hostname to use for the FS image')
    parser.add_argument('--client_id',
        help='DHCP client ID in form "enclosure/X/node/Y"')
    parser.add_argument('--manifest',
        help='Manifest namespace.')
    parser.add_argument('--golden_tar',
        help='Location of pristine FS image tarball')
    parser.add_argument('--packages',
        help='Extra packages to install on new file system')
    parser.add_argument('--build_dir',
        help='Folder where untared FS and compressed images are built.')
    parser.add_argument('--tftp_dir',
        help='Absolute path to the server\'s TFTP folder, images placed here.')

    parser.add_argument('-v', '--verbose',
        help='Make it talk. Verbosity levels from 1 to 5',
        action='store_true')
    parser.add_argument('--debug',
        help='Matrix has you. Enter the debugging mode.',
        action='store_true')

    args, _ = parser.parse_known_args()
    execute(args)

    raise SystemExit(0)
