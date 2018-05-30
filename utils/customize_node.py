#!/usr/bin/python3
"""
  Script that performs a basic set of customizations of a golden image:
- Move kernel from [filesystem_image]/boot/ (not needed for diskless boot)
- Set correct symbolic link for /init file
- Set /etc/hostname
- Set /etc/hosts
- and some other operations.
"""
__author__ = "Rocky Craig, Zakhar Volchak"
__copyright__ = "Copyright 2017 Hewlett Packard Enterprise Development LP"
__maintainer__ = "Rocky Craig, Zakhar Volchak"
__email__ = "rocky.craig@hpe.com, zakhar.volchak@hpe.com"


import argparse
import contextlib
import glob
import gzip
import json
import magic  # to get file type and check if gzipped
import os
import requests as HTTP_REQUESTS
import shutil   # explicit namespace differentiates from our custom FS routines
import sys
import time

from pdb import set_trace

from tmms.utils import core_utils
from tmms.utils import file_utils
from tmms.utils import logging
from tmms.utils import utils

#==============================================================================
# A (custom) kernel will probably only boot itself and not load any modules.
# I have seen a custom kernel force a reload of the original (distro) kernel
# from a dependency cascade of the drivers (zbridge, atomics, tmfs, tmflush).
# I suspect /etc/kernel scripts from the original golden kernel but haven't
# actually tracked it down.   Hasn't been seen in a while....


def extract_bootfiles(args, keep_kernel=False):
    """
        Remove boot/vmlinuz* and boot/initrd.img/ files from new file system.
    These files are not needed in the rootfs for diskless boot.  Move them
    to args.build_dir for future use.  Two or more kernels at any one call
    is an error (no way to choose programmatically).  Let the caller decide
    if zero kernels is an error.

    :param 'args' argparse.Namespace()
        .build_dir: [str] where to move the unecessary files.
        .new_fs_dir': [str] where to find the unecessary files.
        .manifest.keep_kernel: user may choose for keep kernel in boot/

    :param 'keep_kernel': [bool] True - keep, but copy into the build dir.
                                False - move kernel from boot/.
    :return: 'None' on success. Raise 'RuntimeError' on problems.
    """
    boot_dir = '%s/boot/' % args.new_fs_dir
    vmlinuz = glob.glob('%s/vmlinuz*' % (boot_dir))      # Move and keep
    initrd = glob.glob('%s/initrd.img*' % (boot_dir))    # Move and ignore

    is_force_keep_kernel = False
    # 'manifest' param may not exist when building golden image.
    if hasattr(args, 'manifest'):
        #override 'keep_kernel' if user used 'keep_kernel' in the manifest
        is_force_keep_kernel = getattr(args.manifest, 'keep_kernel', False)
        keep_kernel = is_force_keep_kernel

    #Note: also extract config-* and System.map* files installed with kernel.
    misc = glob.glob('%s/config*' % boot_dir)
    misc.extend(glob.glob('%s/System.map*' % boot_dir))

    if len(vmlinuz) > 1:
        if args.debug and sys.stdin.isatty():       # Not forked
            set_trace()
        raise RuntimeError('Multiple (%d) kernels exist! Hostname: %s' % (
            len(vmlinuz), args.hostname))

    if not hasattr(args, 'vmlinuz_golden'):         # singleton
        args.vmlinuz_golden = ''

    extract_type = 'Extract' if not keep_kernel else 'Copy and keep'
    update_status(args, '%s %d /boot/[vmlinuz,initrd]' % (
        extract_type, len(vmlinuz)))

    for source in vmlinuz + initrd + misc:            # move them all
        dest = '%s/%s' % (args.build_dir, os.path.basename(source))
        if keep_kernel:
            file_utils.copy_target_into(source, dest)
        else:
            file_utils.move_target(source, dest)

        if '/vmlinuz' in dest:
            args.vmlinuz_golden = dest

    return vmlinuz + initrd + misc


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
        with file_utils.workdir(args.new_fs_dir):  # At the root
            if os.path.exists('init'):  # no leading slash!!!
                os.unlink('init')
            file_utils.make_symlink('sbin/init', 'init')
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
    #if not os.path.exists(sources_base):
    #    update_status(args, ' - ! - Skipping cleanup_sources_list. No based.list to clean.')
    #    return

    try:
        file_utils.remove_target(sources_base)

        content = [
            '# Created by TMMS for %s on %s' % (args.hostname, time.ctime()),
            '# a.k.a. %s' % args.node_coord,
            'deb %s %s %s' % (args.repo_mirror,
                                args.repo_release,
                                ' '.join(args.repo_areas))
        ]

        file_utils.write_to_file(sources_list, '\n'.join(content))
    except RuntimeError as err:
        raise RuntimeError('clean_sources_list() failed: %s' % str(err))


def set_apt_conf(path, apt_cfg_content, args=None):
    '''
        Set etc/apt/apt.conf content. Usually, it is just PROXY.
    @param path: path to a etc/apt/apt.conf of the build system image.
    @param apt_cfg_content: str (or list) what should go into etc/apt/apt.conf
    '''
    #FIXME: No apt_cfg defaults for corp firewall!
    if not apt_cfg_content:
        if args is not None:
            update_status(args, '- Skipping set_apt_conf. Reason: value is empty.')
        return

    # if a list (each element of which is a line for apt.conf)  was passed, just
    # make it a string joined by new line.
    if isinstance(apt_cfg_content, list):
        apt_cfg_content = '\n'.join(apt_cfg_content)

    #apt.conf doesnt like single quotes. It requires " instead of '.
    #Json format doesn't like ". Thus, when building a apt.conf string in the
    #manifest, a singe ' will be used. Replace it with " and life should be good.
    apt_cfg_content = apt_cfg_content.replace('\'', '"')
    try:
        file_utils.write_to_file(path, apt_cfg_content)
    except RuntimeError as err:
        raise RuntimeError('Could not set_apt_conf content at "%s"! [%s]' % (
                            path, err))


def set_apt_proxy(args):
    """
        @param args: namespace obj.
                --new_fs_dir: dir with untar/ fs dir
                --is_golden: True to skip appending to newly created .conf.
    """
    # FIXME: while called from both tm-manifest setup and tm-manifest-server,
    # runtime environment is quite different and this one set of rules is
    # insufficient.  Either way, get the proxies from os.environ.
    path = args.new_fs_dir + '/etc/apt/apt.conf.d'
    file_utils.make_dir(path)
    path += '/00TMMS.conf'
    args.apt_dot_conf = path    # for post-processing

    # One final post-processing step is done later
    if not args.is_golden:
        return

    # FIXME: it's really dependent on xxx_mirror saying locahost, but this
    # really shouldn't hurt. And don't process 'no_proxy' variable.
    apt_lines = [ 'Acquire::http::proxy::localhost "DIRECT";' ]
    for proxy_type in ('http_proxy', 'https_proxy', 'ftp_proxy'):
        proxy_url = os.environ.get(proxy_type, False)
        if not proxy_url:
            continue
        proxy_type = proxy_type.split('_proxy')[0]
        entry = 'Acquire::%s::proxy "%s";' % (proxy_type, proxy_url)
        apt_lines.append(entry)

    content = '\n'.join(apt_lines)
    update_status(args, 'Adding proxy entries to %s:\n%s\n' % (path, content))
    if not apt_lines:
        return

    try:
        file_utils.write_to_file(path, content)    # Yes, overwrite
    except RuntimeError as err:
        raise RuntimeError('Failed writing proxy settings to %s! Reason:\n- %s' %\
                            (path, err))


def add_other_mirror(args):
    """
    @param other_mirrors:
    """
    args.other_list = '%s/etc/apt/sources.list.d' % args.new_fs_dir
    file_utils.make_dir(args.other_list)
    args.other_list += '/other.list'        # For post-processing

    if not args.is_golden or not hasattr(args, 'other_mirrors'):
        return

    update_status(args, 'Adding other mirrors: %s' % args.other_mirrors)
    if isinstance(args.other_mirrors, str):
        other_mirrors = args.other_mirrors.split(',')
    else:
        other_mirrors = args.other_mirrors
    file_utils.write_to_file(args.other_list, '\n'.join(other_mirrors))
    return


def localhost2torms(args):
    '''Go through apt.conf.d and sources.list.d and change localhost -> torms'''
    if args.is_golden:
        return
    update_status(args, 'Convert APT "localhost" references to "torms"')

    # Always apt.conf, usually other_list
    for fname in (args.apt_dot_conf, args.other_list):
        if os.path.isfile(fname):
            with open(fname, 'r') as f:             # Has newlines...
                lines = ''.join(f.readlines())      # ...so keep them
            file_utils.write_to_file(fname, lines.replace('localhost', 'torms'))

#===========================================================================


def set_client_id(args):
    """
        Augment dhclient configuration file

    :param 'new_fs_dir': [str] path to the file system location to customize.
    :param 'DhcpClientId': [str] calculated elsewhere
    :return: 'None' on success. Raise 'RuntimeError' on problems.
    """
    if getattr(args, 'DhcpClientId', None) is None:
        update_status(args, ' - ! - Skipping "set_client_id"! "DhcpClientId" is None.')
        return

    update_status(args, 'Set ClientID for dhcpc')
    dhclient_conf = '%s/etc/dhcp/dhclient.conf' % args.new_fs_dir
    clientid = args.DhcpClientId
    try:
        with open(dhclient_conf, 'a') as f:
            f.write('\nsend dhcp-client-identifier "%s";\n' % clientid)
    except Exception as err:
        raise RuntimeError('Cannot set DHCP client ID: %s' % str(err))

#==============================================================================


def hack_LFS_autostart(args):
    """
        2016-11-10 SFW is still not supplying ACPI info for physloc but we
    have sufficient need and confidence to require it.  Work around it.
    This must be called before rewrite_rclocal().

    :param 'new_fs_dir': [str] path to the file system location to customize.
    :param 'node_id': [int] expanded into R:E:N.
    :return: 'None' on success. Raise 'RuntimeError' on problems.
    """
    if args.is_golden:
        update_status(args, ' - ! - Skipping hack_lfs_autostart')
        return

    rclocal = ''
    if getattr(args, 'rclocal', None) is not None:
        rclocal = args.rclocal

    update_status(args, 'Hack LFS autostart')
    LFS_conf = '%s/etc/default/tm-lfs' % args.new_fs_dir

    enc = ((args.node_id - 1) // 10) + 1
    node = ((args.node_id - 1) % 10) + 1
    REN = '1:%d:%d' % (enc, node)
    try:
        with open(LFS_conf, 'a') as f:
            f.write('\n\n# Autohack (1) for now, see /etc/rc.local\n')
            f.write("OPT_ARGS='--fakezero --physloc %s'\n" % REN)

        rclocal += '\n# Autohack (2) for now, see /etc/default/tm-lfs\n'
        rclocal += 'systemctl enable tm-lfs\nsystemctl start tm-lfs\n'

        args.rclocal = rclocal
    except Exception as err:    # Not an error, just trouble on node boot
        update_status(args, 'Cannot hack LFS autostart: %s' % str(err))

#==============================================================================

def set_foreign_package(args, foreign_package):
    """
        When "foreign" parameter used in vmdebootstrap, it will remove whose
    packages from the image when done building. However, there are cases when
    those foreign packages need to stay in the image. For example, for manifesting
    to be able to "chroot" to arm image, "qemu-aarch64-static" need to be present
    in the usr/bin directory.

    @param foreign_package: package to get from host's /usr/bin into build image
    """
    foreign_in_build = args.build_dir + '/untar/usr/bin/' + foreign_package
    if not os.path.exists(foreign_in_build):
        file_utils.copy_target_into('/usr/bin/' + foreign_package, foreign_in_build)
        os.chmod(foreign_in_build, 0o755)


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
            file_utils.remove_target(fname)

        content = [ '# Created by TMMS for %s on %s' %
            (args.hostname, time.ctime()) ]
        for var in ('http_proxy', 'https_proxy'):
            val = os.environ.get(var, False)
            if val:
                content.append('%s=%s' % (var, val))

        content = '\n'.join(content)
        file_utils.write_to_file(fname, content)
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
            file_utils.remove_target(hostname_file)
        file_utils.write_to_file(hostname_file, args.hostname)
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
            file_utils.remove_target(fname)

        content = [
            '127.0.0.1   localhost',
            '127.1.0.1   %s' % args.hostname
        ]
        content = '\n'.join(content)

        file_utils.write_to_file(fname, content)
    except RuntimeError as err:
        raise RuntimeError('Cannot set %s: %s' % (fname, str(err)))


def set_resolv_conf(args):
    """
        Copy /etc/resolv.conf from host to the building image.
    """
    update_status(args, 'Setting etc/resolv.cfg')
    resolv_path = '%s/etc/resolv.conf' % (args.new_fs_dir)

    if os.path.islink(resolv_path):
        file_utils.remove_target(resolv_path)

    file_utils.copy_target_into('/etc/resolv.conf', resolv_path)


def set_sudo(args):
    """
        Set sudoer policy of no password for the normal user.  That user was
    configured with sudo in the golden image via vmdebootstrap.  This
    removes the password restriction for easier automation and has been
    approved by Operational Security.  See also set_sshkeys().

    :param 'new_fs_dir': [str] path to the file system location to customize.
    :return: 'None' on success. Raise 'RuntimeError' on problems.
    """
    update_status(args, 'Create /etc/sudoers.d/l4mdc')
    fname = '%s/etc/sudoers.d/l4mdc' % args.new_fs_dir
    try:
        if os.path.exists(fname):
            file_utils.remove_target(fname)

        content = [                             # Speed up subsequent sudos
            'l4mdc\t ALL = NOPASSWD: ALL',      # No passwd
            'l4tm\t ALL = NOPASSWD: ALL',       # Legacy user
            'Defaults timestamp_timeout=120',   # Don't ask again for 2 hours..
            'Defaults !tty_tickets',            # On any terminal
        ]
        file_utils.write_to_file(fname, '\n'.join(content))
    except RuntimeError as err:
        raise RuntimeError('Cannot set %s: %s' % (fname, str(err)))

#==============================================================================
# ssh private and public keys.  At least one demo (LSGi) wants nodes to
# freely ssh between each other.  I don't know if the LDAP miracle will
# allow this, but FAME needs it anyhow.


def _get_userstuff(args, user):
    with file_utils.workdir(args.new_fs_dir):
        file_content = ''
        with open('etc/passwd', 'r') as file_obj:
            file_content = file_obj.read()

        for line in file_content.split('\n'):
            #the first non-root, created User is usually 1000
            if '1000:1000' in line:
                _, _, uid, gid, gecos, home, shell = line.split(':')
                uid = int(uid)
                gid = int(gid)
                return args.new_fs_dir + home, uid, gid
        else:
            raise RuntimeError('Cannot find normal user 1000:1000')


def set_sshkeys(args):
    """
        Add pubkey to /home/<user>/.ssh/authorized_keys.  Overwrite
    /home/<user>/.ssh/id_rsa with privkey.  Where they come from is
    your problem, but ssh-key -t rsa is a good start.

    :param '[l4tm_]privkey': [str] RSA private key, phraseless
    :param '[l4tm_]pubkey':  [str] RSA public key, phraseless
    :return: 'None' on success. Raise 'RuntimeError' on problems.
    """
    update_status(args, 'Set ssh keys for normal user')
    home, uid, gid = _get_userstuff(args, 'l4mdc')
    dotssh = home + '/.ssh'
    os.makedirs(dotssh, mode=0o700, exist_ok=True)
    os.chown(dotssh, uid, gid)

    # Try both for now
    pubkey = getattr(args, 'pubkey', None) or getattr(args, 'l4tm_pubkey', None)
    if pubkey is not None:
        auth = dotssh + '/authorized_keys'
        with open(auth, 'w+') as f:
            f.write('\n')
            f.write(pubkey)
        os.chmod(auth, 0o644)   # pubkey doesn't work if other/world-writeable
        os.chown(auth, uid, gid)
    else:
        update_status(args, ' - ! - ssh pubkey is not set.')

    privkey = getattr(args, 'privkey', None) or getattr(args, 'l4tm_privkey', None)
    if privkey is not None:
        id_rsa = dotssh + '/id_rsa'     # default, simplifies config file
        with open(id_rsa, 'w') as f:
            f.write(privkey)
        os.chmod(id_rsa, 0o400)
        os.chown(id_rsa, uid, gid)

        config = dotssh + '/config'
        with open(config, 'w') as f:
            f.write('# From Manifesting\n\nStrictHostKeyChecking no\n')
        os.chmod(config, 0o400)
        os.chown(config, uid, gid)
    else:
        update_status(args, ' - ! - ssh privkey is not set.')

#==============================================================================


def rewrite_rclocal(args):
    """
        Completely rewrite the /etc/rc.local noop script.

    :param 'rclocal': Full script to add, #!/bin/bash is done for you
    :return: 'None' on success. Raise 'RuntimeError' on problems.
    """
    if getattr(args, 'rclocal', None) is None:
        update_status(args, ' - ! - Skipping "rewrite_rclocal"! "rclocal" in "args" is None.')
        return

    if getattr(args, 'manifest', None) is None:
        update_status(args, ' - ! - Skipping "rewrite_rclocal"! "manifest" in "args" is None.')
        return

    update_status(args, 'Rewriting /etc/rc.local')

    rclocal = '%s/etc/rc.local' % (args.new_fs_dir)
    with open(rclocal, 'w') as f:
        f.write('#!/bin/bash\n\n# Rewritten via manifest %s\n\n' %
            args.manifest.namespace)
        f.write('PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin\n\n')
        f.write('\n%s\n' % args.rclocal)
        f.write('\nexit 0\n')

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
        found_data = core_utils.find(
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
            with file_utils.workdir(args.new_fs_dir):
                ret, cpio_out, cpio_err = core_utils.piper(
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


_dpkgItemplate = '''
dpkg -i {0}
RET=$?
if [ $RET -eq 0 ]; then
    [ "False" = "{1}" ] && rm {0}   # "False" = "--debug flag"
else
    # Most likely: dependencies for {0}
    echo "dpkg -i {0} had problems, return value = $RET" >&2
    apt-get -f -y --force-yes install
    RET=$?
    [ $RET -ne 0 ] && echo "Cleanup {0} problems, return value = $RET" >&2
fi
'''


def install_packages(args):
    """
        Install list of packages into the filesystem image.
    Function will generate a bash script with lines of "apt-get install"
    in it.   This script is placed under the file system. Then, this function
    will execute this script under the chrooted to "args.new_fs_dir". Also,
    every action performed by generated install.sh script is logged into the
    'args.new_fs_dir + "/manifesting.log"' file.

    :param 'args.new_fs_dir': [str] path to filesystem image to customize.
    :param 'args.packages': [str] of packages 'apt-get install'.
    :param 'args.tasks': [list] of tasks for 'tasksel'.
    :return [boolean] True if it worked, False otherwise with updated status.
    """
    is_debug = getattr(args, 'debug', False)
    localdebs = None
    packages = None
    downloads = None

    # Separate the space-delimited list of packages into URLs and package names
    if args.packages is None:
        msg = 'Updating/upgrading packages from golden image'
    else:
        if ',' in args.packages:
            pkglist = args.packages.replace(' ', '').split(',')
        else:
            pkglist = args.packages.split(' ')

        localdebs = [p for p in pkglist if p.startswith('file://') ]
        downloads = [p for p in pkglist if
            (p.startswith('http://') or p.startswith('https://'))]
        _debs = localdebs + downloads
        packages = [p for p in pkglist if p not in _debs]

        msg = 'Installing %d packages plus %d URL downloads and %d local debs' % (
            len(packages), len(downloads), len(localdebs))
        msg += '\n - pkgs: %s\n - downloads: %s\n - localdebs: %s' %\
                (packages, downloads, localdebs)

    update_status(args, msg)

    # Some packages need this (python-mon-agent)
    if getattr(args, 'tmconfig', None) is not None:
        shutil.copy(args.tmconfig, args.new_fs_dir + '/etc/tmconfig')

    # Fill out the install script.  Everything goes at root $HOME.
    installsh = '/root/install.sh'
    installog = '/root/install.log'
    script_file = args.new_fs_dir + installsh
    log_file = args.new_fs_dir + installog

    # In case the script never gets built properly
    with open(log_file, 'w') as prelog:
        prelog.write(
            'Logic errors in customization kept %s from being created' %
        installsh)

    # Don't use "-e" (exit on error).  It always does "exit 1" which gets
    # treated as EPERM, masking the real error.  It's also inherited by
    # subshells which mask things even further.

    script_header = """#!/bin/bash
# Created %s
set -u
cd /root
exec > %s 2>&1
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get upgrade -q --assume-yes -y --force-yes
# apt-get dist-upgrade -q --assume-yes

echo "en_US UTF-8" > /etc/locale.gen
/usr/sbin/locale-gen
# I can't get the previous steps to accomplish this...something is missing?
echo 'LANG="en_US.UTF-8"' >> /etc/default/locale
""" % (time.ctime(), installog)

    with open(script_file, 'w') as install:
        # install.write("this isn't legal this cannot work\n")
        install.write(script_header)

        install.write('\n# Packages: %s\n' % packages)
        if packages is not None:
            for pkg in packages:
                install.write(
                    '\necho -e "\\n---------- Installing %s\\n"\n' % pkg)
                cmd = 'apt-get install -q -y --reinstall --force-yes -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" %s\n' % pkg
                install.write(cmd)
                # Things from the repo OUGHT to work.
                install.write(
                    '[ $? -ne 0 ] && echo "Install %s failed" && exit 1\n' %
                    pkg)

        tasks = getattr(args, 'tasks', None)
        install.write('\n# Tasks: %s\n' % tasks)
        if tasks is not None:
            for task in tasks.split(','):
                install.write(
                    '\necho -e "\\n---------- Executing task  %s\\n"\n' % task)
                cmd = 'tasksel install %s\n' % task
                install.write(cmd)
                # Things from the repo OUGHT to work.
                install.write(
                    '[ $? -ne 0 ] && echo "Tasksel %s failed" && exit 1' %
                    task)

        # These are one-offs so relax the expectation of correctness
        if downloads is not None:
            install.write('\n# Show me the Debians! (%d)\n' % len(downloads))
            for pkg in downloads:
                install.write(
                    '\necho -e "\\n---------- Download/install %s\\n"\n' % pkg)
                deb = pkg.split('/')[-1]
                install.write('# %s\n' % deb)
                pkgresp = HTTP_REQUESTS.get(pkg, verify=False)
                if pkgresp.status_code != 200:
                    msg = 'Status %d: could not download "%s"' % (
                        pkgresp.status_code, pkg)
                    args.logger.error(msg)
                    install.write('# %s\n\n' % msg)
                    continue

                with open(args.new_fs_dir + '/root/' + deb, 'wb') as debian:
                    debian.write(pkgresp.content)

                # Log the failures but don't abort the image build.
                dpkgIstr = _dpkgItemplate.format(deb, str(bool(is_debug)))
                install.write(dpkgIstr)

        if localdebs is not None:
            install.write('\n# Even MORE Debians! (%d)\n' % len(localdebs))
            targetdir = args.new_fs_dir + '/root'
            for pkg in localdebs:
                install.write(
                    '\necho -e "\\n---------- Local copy of %s\\n"\n' % pkg)
                install.write('# %s\n' % pkg)
                src = pkg.split('file://')[-1]
                deb = pkg.split('/')[-1]
                install.write('# %s\n' % deb)
                shutil.copy(src, targetdir)
                dpkgIstr = _dpkgItemplate.format(deb, str(bool(is_debug)))
                install.write(dpkgIstr)

        if getattr(args, 'postinst', None) is not None:
            install.write('\n# "postinst" scriptlet from manifest\n\n')
            install.write(args.postinst + '\n')

        # Release cache space (megabytes).  DON'T use autoclean, it increases
        # the used space (new indices?)
        install.write('\necho systemctl status says...\n')
        install.write('\nsystemctl status\n')
        install.write('\necho chroot installer complete at `date`\n')
        install.write('\nexec apt-get clean\n')     # Final exit value

    os.chmod(script_file, 0o744)

    try:
        procmount = args.new_fs_dir + '/proc'
        os.makedirs(procmount, exist_ok=True)
        ret, stdout, sterr = core_utils.piper('mount -obind /proc ' + procmount)
        assert not ret, 'Cannot bind mount /proc'

        umount = 'umount -fl %s' % procmount

        ptsmount = args.new_fs_dir + '/dev/pts'
        os.makedirs(ptsmount, exist_ok=True)
        ret, stdout, sterr = core_utils.piper('mount -obind /dev/pts ' + ptsmount)
        assert not ret, 'Cannot bind mount /dev/pts'

        umount = 'umount -fl %s %s' % (procmount, ptsmount)

        # In case the script never gets to run.
        with open(log_file, 'w') as prelog:
            prelog.write(
                'Syntax errors in %s kept it from ever running' % installsh)

        cmd = '/usr/sbin/chroot %s /bin/bash -c %s' % (
            args.new_fs_dir, installsh)
        # This can take MINUTES, ie, "album" pulls in about 80 more packages.
        # While running, sys-images/nodeXX/untar/root/install.log is updated.
        # Hopefully install.sh catches its own errors
        ret, stdout, stderr = core_utils.piper(cmd, use_call=True)
        if ret:
            stdouterr = ''
            if stdout is not None:
                stdouterr += str(stdout) + '\n'
            if stderr is not None:
                stdouterr += str(stderr) + '\n'
            raise RuntimeError(
                'chroot install.sh retval=%d: %s' % (ret, stdouterr))
        return True     # but see finally
    except Exception as err:
        args.logger.error( '%s' % (err))
        with open(args.new_fs_dir + installog, 'r') as log:
            args.logger.debug(' - D - %s' % log.read())
        raise RuntimeError(str(err))
    finally:
        umountret, _, _ = core_utils.piper(umount)
        utils.kill_chroot_daemons(args.build_dir)
    return False


def customize_grub(args):
    """
        COnfigure grub's config entry with a custom kernel command line (if
    presented in the manifest).
    """
    if getattr(args, 'manifest', None) is None:
        update_status(args, ' - ! - Skipping "customize_grub"! "manifest" is None.')
        return

    if getattr(args, 'tftp_dir', None) is None:
        update_status(args, ' - ! - Skipping "customize_grub"! "tftp_dir" is None.')
        return

    kernel_cmd = args.manifest.thedict.get('kernel_append', None)
    if (kernel_cmd is None):
        kernel_cmd = 'rw earlycon=pl011,0x402020000 ignore_loglevel'
    try:
        from tmms.templates import networking
    except ImportError as err:
        raise RuntimeError('Failed to import grub template for networking configs!')
    grub_menu = networking.grub_menu.render(hostname=args.hostname,
                                images_dir='/images/' + args.hostname,
                                append=kernel_cmd)
    destination = args.tftp_dir + '/../../grub/menus/' + args.hostname + '.menu'
    with open(destination, 'w') as file_obj:
        file_obj.write(grub_menu)

#==============================================================================


def update_status(args, message, status='building'):
    """
        Update status of the node at the given state in its tftp/images/nodeX
    directory.
        Status must be one of 'building', 'ready', or 'error'
    """
    if getattr(args, 'dryrun', False):
        return
    # Message is either a dict or a string
    level = 'info'
    try:
        if message['status'] >= 300:
            level = status = 'error'
        message = message['message']
    except Exception as e:
        pass
    args.logger('%s' % message, level=level)

    response = {}
    if getattr(args, 'manifest', None) is None:
        response['manifest'] = 'Not set'
    else:
        response['manifest'] = args.manifest.namespace

    response['status'] = status
    response['message'] = message
    response['coordinate'] = args.node_coord    # Troubleshooting and QA
    response['DhcpClientId'] = getattr(args, 'DhcpClientId', 'Not set')
    response['node_id'] = getattr(args, 'node_id', 'Not set')
    response['hostname'] = args.hostname

    # Rally DE118: make it an atomic update
    newstatus = args.status_file + '.new'
    file_utils.write_to_file(newstatus, json.dumps(response, indent=4))
    os.replace(newstatus, args.status_file)

#=============================================================================
# ESP == EFI System Partition, where EFI wants to scan for FS0:.


def create_ESP(args, blockdev, vmlinuz, cpio):
    update_status(args, 'Creating and filling ESP')
    ESP_mnt = '%s/mnt' % (args.build_dir)   # Going to be a VFAT FS image
    file_utils.remove_target(ESP_mnt)
    os.makedirs(ESP_mnt)

    # tftp_dir has "images/nodeZZ" tacked onto it from caller.
    # Grub itself is pulled live from a fixed location.
    # Plain grubaa64.efi was built with prefix "/EFI/debian" as opposed
    # to the '/grub' of grubnetaa64.efi.  In either case, grub[net]aa64.efi
    # turns around and grabs <prefix>/grub.cfg, where "prefix" was set at
    # grub construction.
    follow_Linns_advice = True
    if follow_Linns_advice:
        grubbase = 'grubaa64.efi'
        prefix = '/EFI/debian'
    else:
        grubbase = 'grubnetaa64.efi'    # gzipped files still choke it
        prefix = '/grub'
    getgrub = '/'.join(args.tftp_dir.split('/')[:-2]) + '/grub/%s' % grubbase
    grubdir = ESP_mnt + prefix

    undo_mount = False
    try:
        # This happens on containers. I think I solved it but paranoia is ok.
        assert os.path.exists(blockdev), \
            'Cannot find mapper file %s' % blockdev

        cmd = 'mkfs.vfat ' + blockdev
        ret, stdout, stderr = core_utils.piper(cmd)
        assert not ret, cmd

        # Step 3: Make, mount, and fill the VFAT FS.  The EFI default startup
        # script goes at /, but the grub stuff lives under "prefix".

        cmd = 'mount %s %s' % (blockdev, ESP_mnt)
        ret, stdout, stderr = core_utils.piper(cmd)
        assert not ret, cmd
        undo_mount = True
        update_status(args, 'SDHC GRUB DIR established at %s' % grubdir)

        # The EFI directory separator is backslash, while grub is forward.
        with open(ESP_mnt + '/startup.nsh', 'w') as f:
            f.write(prefix.replace('/', '\\') + '\\%s\n' % grubbase)
        os.makedirs(grubdir)
        shutil.copy(vmlinuz, grubdir)
        shutil.copy(cpio, grubdir)
        shutil.copy(getgrub, grubdir)

        with open(grubdir + '/grub.cfg', 'w') as f:
            # Originally for SNBU but worth keeping
            f.write('set debug=linux,linuxefi,efi\n')
            f.write('set pager=1\n')
            f.write('linux %s/%s\n' % (prefix, os.path.basename(vmlinuz)))
            f.write('initrd %s/%s\n' % (prefix, os.path.basename(cpio)))
            f.write('boot\n')

    except Exception as e:
        pass    # Just keep it here

    if undo_mount:
        cmd = 'umount ' + ESP_mnt
        ret, stdout, stderr = core_utils.piper(cmd)
        assert not ret, cmd

    return undo_mount   # suppress final copy if this didn't work

#=============================================================================
# SNBU == Single Node Bringup, the first turnon of node boards.
# It will get burned onto SDHC/USB for single node bringup (SNBU).
# This will be pulled over HTTP, dd'd, etc.  Keep it small but useful.
# Most cpio.gz are under 200M, vmlinuz.gz under 7M, so this leaves
# at least 50M of space for copying log files, etc.  SNBU shouldn't
# make all that much data, he says with a smile.


def create_SNBU_image(args, vmlinuz, cpio):
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
        ret, stdout, stderr = core_utils.piper(cmd)
        assert not ret, cmd

        # Step 2: located the partition and create a block device.
        # Ass-u-me enough loopback devics to go around.

        cmd = 'kpartx -asv %s' % ESP_img
        ret, stdout, stderr = core_utils.piper(cmd)
        assert not ret, cmd
        undo_kpartx = True
        stdout = stdout.decode()
        assert stdout.startswith('add map loop'), \
            'Unexpected kpartx output: %s' % stdout
        blockdev = '/dev/mapper/' + stdout.split()[2]
        assert blockdev.endswith('p1'), \
            'Unexpected kpartx partition: %s' % blockdev

        # Step 3: fill it out

        do_copy = create_ESP(args, blockdev, vmlinuz, cpio)

    except AssertionError as e:
        args.logger.error('%s failed:\n - errno = %d: %s' % (
                        str(e), ret, stderr))
    except RuntimeError as e:
        args.logger.error('%s:\n - errno = %d: %s' % (
                        str(e), ret, stderr))
    except Exception as e:
        args.logger.critical('%s:\n - errno = %d: %s' % (
                        str(e), ret, stderr))

    if undo_kpartx:
        # Sometimes this fails, especially with overloaded/underpowered
        # server and "setnodes all".   Early in diagnosis, not sure what
        # to do about it.   Just move along for now and see what happens
        cmd = 'kpartx -d %s' % ESP_img
        ret, stdout, stderr = core_utils.piper(cmd)
        # assert not ret, cmd
        if ret or stderr:
            args.logger.warning('kpartx -d returned %d:\n - %s' % (ret, stderr))

    if do_copy:
        try:
            shutil.copy(ESP_img, args.tftp_dir)
        except OSError:
            return
        except Exception as err:
            msg = ' - ERROR - Unexpected error duing create_SNBU_image:'
            msg += '\n -- last step duing shutil.copy: %s' % err;
            update_status(args, msg)
            return

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
# For kernels, the name of the file (vmlinuz vs vmlinux, .gz or no .gz) is
# no indication if it's already compressed.  While compressing again is
# legal, the dual-compression makes grub very sad.  Check first.


def _is_gzipped(fname):
    '''
        Check "gzip" word in file's type string using python3-magic module.
    Source: https://stackoverflow.com/questions/25286176/how-to-use-python-magic-5-19-1
    '''
    try:
        magic_obj = magic.open(magic.MAGIC_NONE)
        magic_obj.load()
        file_type_str = magic_obj.file(fname).lower()
        return 'gzip' in file_type_str
    except OSError:
        return False
    except Exception as err:
        raise RuntimeError('Failed in _is_gzipped(%s)! Error: %s' % (fname, err))


def compress_bootfiles(args, cpio_file):
    update_status(args, 'Compressing kernel and file system')
    vmlinuz_gzip = args.tftp_dir + '/' + args.hostname + '.vmlinuz.gz'
    if _is_gzipped(args.vmlinuz_golden):
        shutil.copy(args.vmlinuz_golden, vmlinuz_gzip)
    else:
        with open(args.vmlinuz_golden, 'rb') as f_in:
            with gzip.open(vmlinuz_gzip, mode='wb', compresslevel=6) as f_out:
                shutil.copyfileobj(f_in, f_out)

    cpio_gzip = args.tftp_dir + '/' + os.path.basename(cpio_file) + '.gz'
    if _is_gzipped(cpio_file):
        shutil.copy(cpio_file, cpio_gzip)
    else:
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
    if not os.path.exists(args.build_dir):
        file_utils.make_dir(args.build_dir)

    #set defaults
    if getattr(args, 'debug', None) is None:
        args.debug = False
    if getattr(args, 'verbose', None) is None:
        args.verbose = False
    if getattr(args, 'is_golden', None) is None:    # set in setup_golden.py
        args.is_golden = False

    logger = getattr(args, 'logger', None)

    if not args.debug:
        # Ass-u-me I am the first child in a fork-setsid-fork daemon chain
        try:
            os.chdir('/tmp')
            os.setsid()
            forked = os.fork()
            if logger is not None:
                args.logger.debug('Spawning parent PID=%s' % (forked))
            # Release the wait that should be done by original parent
            if forked > 0:
                if logger is not None:
                    args.logger.debug('Closing parent PID=%s.' % (forked))

                os._exit(0)  # RTFM: this is the preferred exit after fork()

                if logger is not None:
                    args.logger.debug('Rocky\'s rookie spawned a rookie')
        except OSError as err:
            if logger is not None:
                args.logger.critical('Failed to spawn a child: %s ' % str(err))
            raise RuntimeError(
                'Rocky\'s rookie\'s rookie is down! Bad Luck. [%s]' % str(err))

    response = {  # No errors occured yet! Let's keep it this way.
        'status': 200,
        'message': 'System image was created.'
    }
    status = None   # Establish scope prior to possible Except clause

    # Replace the logger after parent may have closed extra fds
    fname='%s/build.log' % args.build_dir
    if logger is not None:
        args.logger.info(' --- Build details in %s ---' % fname)

    logger = logging.tmmsLogger(args.hostname, use_file=fname)
    logger.propagate = args.verbose     # always gets forced True at end
    args.logger = None
    args.logger = logger

    args.logger('--- Starting image build for %s --- ' % args.hostname)
    # It's a big try block because individual exception handling
    # is done inside those functions that throw RuntimeError.
    # When some of them fail they'll handle last update_status themselves.
    try:
        update_status(args, 'Untar golden image')
        args.new_fs_dir = core_utils.untar(args.build_dir + '/untar/', args.golden_tar)

        # Move kernel that comes with golden image.
        extract_bootfiles(args, args.is_golden)

        set_foreign_package(args, 'qemu-aarch64-static')

        # Golden image contrived args has no "manifest" attribute.  Besides,
        # a manifest should not contain distro-specific data structures.
        cleanup_sources_list(args)
        set_apt_proxy(args)
        add_other_mirror(args)

        # Global and account config files
        set_resolv_conf(args)

        set_environment(args)
        set_hostname(args)
        set_hosts(args)
        set_client_id(args)
        set_sudo(args)
        set_sshkeys(args)

        install_packages(args)

        #Move installed "kernel" from boot/ (if any).
        extract_bootfiles(args, args.is_golden)
        assert args.vmlinuz_golden, 'No golden/add-on kernel can be found'

        persist_initrd(args)

        localhost2torms(args)
        hack_LFS_autostart(args)    # Temporary; must come before...
        rewrite_rclocal(args)

        #------------------------------------------------------------------

        if args.is_golden:
            response['message'] = 'Golden image ready for use'
            status = 'ready'
        else:
            cpio_file = create_cpio(args)
            vmlinuz_gzip, cpio_gzip = compress_bootfiles(args, cpio_file)
            create_SNBU_image(args, vmlinuz_gzip, cpio_gzip)

            # Free up space someday, but not during active development
            # remove_target(args.build_dir)
            # Leave a copy of the controlling manifest for post-mortems
            if getattr(args, 'manifest', None) is not None:
                manifest_tftp_file = args.manifest.namespace.replace('/', '.')
                file_utils.copy_target_into(args.manifest.fullpath,
                                args.tftp_dir + '/' + manifest_tftp_file)

            update_status(args, 'Updating grub menu for the node.')
            customize_grub(args)

            response['message'] = 'PXE files ready to boot'
            status = 'ready'

    except AssertionError as err:   # Consistency check
        response['status'] = 505
        response['message'] = 'Consistency failure: %s' % str(err)
        status = 'error'
    except RuntimeError as err:     # Caught earlier and re-thrown as this
        response['status'] = 505
        response['message'] = 'Filesystem image build failed: %s' % str(err)
        status = 'error'
    except Exception as err:        # Suppress Flask traceback
        response['status'] = 505
        response['message'] = '%s:%s:\nUnexpected error: %s' %\
            (os.path.basename(__file__), sys.exc_info()[2].tb_lineno, str(err))
        status = 'error'

    args.logger.propagate = True   # push final messages to root logger
    update_status(args, response, status)
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
                        help='Name for the build image. (old: Full machine coordinate of this node.')
    parser.add_argument('--node_id', default=None,
                        help='Node number (1-40)."')
    parser.add_argument('--manifest', default=None,
                        help='Manifest namespace.')
    parser.add_argument('--golden_tar',
                        help='Location of pristine FS image tarball')
    parser.add_argument('--repo_mirror',
                        help='URL of Debian mirror')
    parser.add_argument('--repo_release',
                        help='release to use on mirror')
    parser.add_argument('--repo_areas',
                        help='areas to use from a release on mirror')
    parser.add_argument('--packages', default=None,
                        help='Extra packages to "apt-get install" on new FS.')
    parser.add_argument('--tasks', default=None,
                        help='Tasks to "tasksel install" on new FS.')
    parser.add_argument('--build_dir',
                        help='Scratch folder for building FS images.')
    parser.add_argument('--tftp_dir', default=None,
                        help='Absolute path to the dnsmasq TFTP folder.')
    parser.add_argument('-v', '--verbose',
                        help='Make it talk. Verbosity levels from 1 to 5',
                        action='store_true')
    args, _ = parser.parse_known_args()

    args.debug = True  # suppress daemonization
    execute(args)

    raise SystemExit(0)
