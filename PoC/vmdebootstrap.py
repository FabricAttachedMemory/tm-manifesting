#! /usr/bin/python
# Copyright 2011-2013  Lars Wirzenius
# Copyright 2012  Codethink Limited
# Copyright 2014 Neil Williams <codehelp@debian.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import cliapp
import crypt
import logging
import os
import re
import shutil
import subprocess
import tempfile
import time

from pdb import set_trace

__version__ = '0.5'


class VmDebootstrap(cliapp.Application):

    def add_settings(self):
        default_arch = subprocess.check_output(
            ["dpkg", "--print-architecture"]).strip()

        self.settings.boolean(['verbose'], 'report what is going on')
        self.settings.string(['image'], 'put created disk image in FILE',
                             metavar='FILE')
        self.settings.bytesize(['size'],
                               'create a disk image of size SIZE (%default)',
                               metavar='SIZE',
                               default='1G')
        self.settings.bytesize(['bootsize'],
                               'create boot partition of size SIZE (%default)',
                               metavar='BOOTSIZE',
                               default='0%')
        self.settings.string(['boottype'],
                             'specify file system type for /boot/',
                             default='ext2')
        self.settings.string(['foreign'],
                             'set up foreign debootstrap environment using provided program (ie binfmt handler)')
        self.settings.string(['variant'],
                             'select debootstrap variant it not using the default')
        self.settings.boolean(['extlinux'], 'install extlinux?', default=True)
        self.settings.string(['tarball'], "tar up the disk's contents in FILE",
                             metavar='FILE')
        self.settings.string(['mirror'],
                             'use MIRROR as package source (%default)',
                             metavar='URL',
                             default='http://http.debian.net/debian/')
        self.settings.string(['arch'], 'architecture to use (%default)',
                             metavar='ARCH',
                             default=default_arch)
        self.settings.string(['distribution'],
                             'release to use (%default)',
                             metavar='NAME',
                             default='stable')
        self.settings.string_list(['package'], 'install PACKAGE onto system')
        self.settings.string_list(['custom-package'],
                                  'install package in DEB file onto system '
                                  '(not from mirror)',
                                  metavar='DEB')
        self.settings.boolean(['no-kernel'], 'do not install a linux package')
        self.settings.boolean(['enable-dhcp'], 'enable DHCP on eth0')
        self.settings.string(['root-password'], 'set root password',
                             metavar='PASSWORD')
        self.settings.boolean(['lock-root-password'],
                              'lock root account so they cannot login?')
        self.settings.string(['customize'],
                             'run SCRIPT after setting up system',
                             metavar='SCRIPT')
        self.settings.string(['hostname'],
                             'set name to HOSTNAME (%default)',
                             metavar='HOSTNAME',
                             default='debian')
        self.settings.string_list(['user'],
                                  'create USER with PASSWORD',
                                  metavar='USER/PASSWORD')
        self.settings.boolean(['serial-console'],
                              'configure image to use a serial console')
        self.settings.string(['serial-console-command'],
                             'command to manage the serial console, appended '
                             'to /etc/inittab (%default)',
                             metavar='COMMAND',
                             default='/sbin/getty -L ttyS0 115200 vt100')
        self.settings.boolean(['sudo'],
                              'install sudo, and if user is created, add them '
                              'to sudo group')
        self.settings.string(['owner'],
                             'the user who will own the image when the build '
                             'is complete.')
        self.settings.boolean(['squash'],
                              'use squashfs on the final image.')
        self.settings.boolean(['configure-apt'],
                              'Create an apt source based on the distribution '
                              'and mirror selected.')
        self.settings.boolean(['mbr'],
                              'Run install-mbr (default if extlinux used)')
        self.settings.boolean(['grub'],
                              'Install and configure grub2 - disables '
                              'extlinux.')
        self.settings.boolean(['sparse'],
                'Dont fill the image with zeros to keep a sparse disk image',
                default=False)

    def process_args(self, args):
        if not self.settings['image'] and not self.settings['tarball']:
            raise cliapp.AppException('You must give disk image filename, '
                                      'or tarball filename')
        if self.settings['image'] and not self.settings['size']:
            raise cliapp.AppException('If disk image is specified, '
                                      'You must give image size.')

        self.remove_dirs = []
        self.mount_points = []

        try:
            rootdev = None
            roottype = 'ext4'
            bootdev = None
            boottype = None
            rootdir = None
            if self.settings['image']:
                self.create_empty_image()
                self.partition_image()
                if self.settings['mbr'] or self.settings['extlinux']:
                    self.install_mbr()
                (rootdev, bootdev) = self.setup_kpartx()
                self.mkfs(rootdev, type=roottype)
                rootdir = self.mount(rootdev)
                if bootdev:
                    if self.settings['boottype']:
                        boottype = self.settings['boottype']
                    else:
                        boottype = 'ext2'
                    self.mkfs(bootdev, type=boottype)
                    bootdir = '%s/%s' % (rootdir, 'boot/')
                    os.mkdir(bootdir)
                    bootdir = self.mount(bootdev, bootdir)
            else:
                rootdir = self.mkdtemp()
            self.debootstrap(rootdir)
            self.set_hostname(rootdir)
            self.create_fstab(rootdir, rootdev, roottype, bootdev, boottype)
            self.install_debs(rootdir)
            self.cleanup_apt_cache(rootdir)
            self.set_root_password(rootdir)
            self.create_users(rootdir)
            self.remove_udev_persistent_rules(rootdir)
            self.setup_networking(rootdir)
            if self.settings['configure-apt']:
                self.configure_apt(rootdir)
            self.customize(rootdir)
            self.update_initramfs(rootdir)

            if self.settings['image']:
                if self.settings['grub']:
                    self.install_grub2(rootdev, rootdir)
                elif self.settings['extlinux']:
                    self.install_extlinux(rootdev, rootdir)
                self.append_serial_console(rootdir)
                self.optimize_image(rootdir)
                if self.settings['squash']:
                    self.squash()

            if self.settings['foreign'] and False:
                os.unlink('%s/usr/bin/%s' %
                          (rootdir, os.path.basename(self.settings['foreign'])))

            if self.settings['tarball']:
                self.create_tarball(rootdir)

            if self.settings['owner']:
                self.chown(rootdir)
        except BaseException, e:
            self.message('EEEK! Something bad happened...')
            if rootdir:
                db_log = os.path.join(rootdir, 'debootstrap', 'debootstrap.log')
                if os.path.exists(db_log):
                    shutil.copy(db_log, os.getcwd())
            self.message(e)
            self.cleanup_system()
            raise
        else:
            self.cleanup_system()

    def message(self, msg):
        logging.info(msg)
        if self.settings['verbose']:
            print msg

    def runcmd(self, argv, stdin='', ignore_fail=False, env=None, **kwargs):
        logging.debug('runcmd: %s %s %s' % (argv, env, kwargs))
        p = subprocess.Popen(argv, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             env=env, **kwargs)
        out, err = p.communicate(stdin)
        if p.returncode != 0:
            msg = 'command failed: %s\n%s\n%s' % (argv, out, err)
            logging.error(msg)
            if not ignore_fail:
                raise cliapp.AppException(msg)
        return out

    def mkdtemp(self):
        dirname = tempfile.mkdtemp()
        self.remove_dirs.append(dirname)
        logging.debug('mkdir %s' % dirname)
        return dirname

    def mount(self, device, path=None):
        if not path:
            mount_point = self.mkdtemp()
        else:
            mount_point = path
        self.message('Mounting %s on %s' % (device, mount_point))
        self.runcmd(['mount', device, mount_point])
        self.mount_points.append(mount_point)
        logging.debug('mounted %s on %s' % (device, mount_point))
        return mount_point

    def create_empty_image(self):
        self.message('Creating disk image')
        self.runcmd(['qemu-img', 'create', '-f', 'raw',
                     self.settings['image'],
                     str(self.settings['size'])])

    def partition_image(self):
        self.message('Creating partitions')
        self.runcmd(['parted', '-s', self.settings['image'],
                     'mklabel', 'msdos'])
        if self.settings['bootsize'] and self.settings['bootsize'] is not '0%':
            bootsize = str(self.settings['bootsize'] / (1024 * 1024))
            self.runcmd(['parted', '-s', self.settings['image'],
                         'mkpart', 'primary', 'fat16', '0%', bootsize])
        else:
            bootsize = '0%'
        self.runcmd(['parted', '-s', self.settings['image'],
                     'mkpart', 'primary', bootsize, '100%'])
        self.runcmd(['parted', '-s', self.settings['image'],
                     'set', '1', 'boot', 'on'])

    def update_initramfs(self, rootdir):
        cmd = os.path.join('usr', 'sbin', 'update-initramfs')
        if os.path.exists(os.path.join(rootdir, cmd)):
            self.message("Updating the initramfs")
            self.runcmd(['chroot', rootdir, cmd, '-u'])

    def install_mbr(self):
        if os.path.exists("/sbin/install-mbr"):
            self.message('Installing MBR')
            self.runcmd(['install-mbr', self.settings['image']])
        else:
            msg = "mbr enabled but /sbin/install-mbr not found"
            " - please install the mbr package."
            raise cliapp.AppException(msg)


    def setup_kpartx(self):
        out = self.runcmd(['kpartx', '-avs', self.settings['image']])
        if self.settings['bootsize']:
            bootindex = 0
            rootindex = 1
            parts = 2
        else:
            rootindex = 0
            parts = 1
            boot = None
        devices = [line.split()[2]
                   for line in out.splitlines()
                   if line.startswith('add map ')]
        if len(devices) != parts:
            raise cliapp.AppException('Surprising number of partitions')
        root = '/dev/mapper/%s' % devices[rootindex]
        if self.settings['bootsize']:
            boot = '/dev/mapper/%s' % devices[bootindex]
        return (root, boot)

    def mkfs(self, device, type):
        self.message('Creating filesystem %s' % type)
        self.runcmd(['mkfs', '-t', type, device])

    def debootstrap(self, rootdir):
        self.message('Debootstrapping')

        if self.settings['foreign']:
            necessary_packages = []
        else:
            necessary_packages = ['acpid']

        if self.settings['grub']:
            necessary_packages.append('grub2')

        include = self.settings['package']

        if not self.settings['no-kernel']:
            if self.settings['arch'] == 'i386':
                kernel_arch = '486'
            else:
                kernel_arch = self.settings['arch']
            kernel_image = 'linux-image-%s' % kernel_arch
            include.append(kernel_image)

        if self.settings['sudo'] and 'sudo' not in include:
            include.append('sudo')

        args = ['debootstrap', '--arch=%s' % self.settings['arch']]
        args.append('--keep-debootstrap-dir')
        # if self.settings['package'] and len(necessary_packages) > 0:
        args.append(
                '--include=%s' % ','.join(necessary_packages + include))
        if self.settings['foreign']:
            args.append('--foreign')
        if self.settings['variant']:
            args.append('--variant')
            args.append(self.settings['variant'])
        args += [self.settings['distribution'],
                 rootdir, self.settings['mirror']]
        logging.debug(" ".join(args))
        print(args)
        self.runcmd(args)
        if self.settings['foreign']:
            # set a noninteractive debconf environment for secondstage
            env = {
                "DEBIAN_FRONTEND": "noninteractive",
                "DEBCONF_NONINTERACTIVE_SEEN": "true",
                "LC_ALL": "C"
            }
            # add the mapping to the complete environment.
            env.update(os.environ)
            # First copy the binfmt handler over
            self.message('Setting up binfmt handler')
            shutil.copy(self.settings['foreign'], '%s/usr/bin/' % rootdir)
            # Next, run the package install scripts etc.
            self.message('Running debootstrap second stage')
            self.runcmd(['chroot', rootdir,
                         '/debootstrap/debootstrap', '--second-stage'],
                        env=env)

    def set_hostname(self, rootdir):
        hostname = self.settings['hostname']
        with open(os.path.join(rootdir, 'etc', 'hostname'), 'w') as f:
            f.write('%s\n' % hostname)

        etc_hosts = os.path.join(rootdir, 'etc', 'hosts')
        try:
            with open(etc_hosts, 'r') as f:
                data = f.read()
            with open(etc_hosts, 'w') as f:
                for line in data.splitlines():
                    if line.startswith('127.0.0.1'):
                        line += ' %s' % hostname
                    f.write('%s\n' % line)
        except IOError, e:
            pass

    def create_fstab(self, rootdir, rootdev, roottype, bootdev, boottype):
        def fsuuid(device):
            out = self.runcmd(['blkid', '-c', '/dev/null', '-o', 'value',
                               '-s', 'UUID', device])
            return out.splitlines()[0].strip()

        if rootdev:
            rootdevstr = 'UUID=%s' % fsuuid(rootdev)
        else:
            rootdevstr = '/dev/sda1'

        if bootdev:
            bootdevstr = 'UUID=%s' % fsuuid(bootdev)
        else:
            bootdevstr = None

        fstab = os.path.join(rootdir, 'etc', 'fstab')
        with open(fstab, 'w') as f:
            f.write('proc /proc proc defaults 0 0\n')
            f.write('%s / %s errors=remount-ro 0 1\n' % (rootdevstr, roottype))
            if bootdevstr:
                f.write('%s /boot %s errors=remount-ro 0 2\n' % (bootdevstr, boottype))

    def install_debs(self, rootdir):
        if not self.settings['custom-package']:
            return
        self.message('Installing custom packages')
        tmp = os.path.join(rootdir, 'tmp', 'install_debs')
        os.mkdir(tmp)
        for deb in self.settings['custom-package']:
            shutil.copy(deb, tmp)
        filenames = [os.path.join('/tmp/install_debs', os.path.basename(deb))
                     for deb in self.settings['custom-package']]
        out, err, exit = \
            self.runcmd_unchecked(['chroot', rootdir, 'dpkg', '-i'] + filenames)
        logging.debug('stdout:\n%s' % out)
        logging.debug('stderr:\n%s' % err)
        out = self.runcmd(['chroot', rootdir,
                          'apt-get', '-f', '--no-remove', 'install'])
        logging.debug('stdout:\n%s' % out)
        shutil.rmtree(tmp)

    def cleanup_apt_cache(self, rootdir):
        out = self.runcmd(['chroot', rootdir, 'apt-get', 'clean'])
        logging.debug('stdout:\n%s' % out)

    def set_root_password(self, rootdir):
        if self.settings['root-password']:
            self.message('Setting root password')
            self.set_password(rootdir, 'root', self.settings['root-password'])
        elif self.settings['lock-root-password']:
            self.message('Locking root password')
            self.runcmd(['chroot', rootdir, 'passwd', '-l', 'root'])
        else:
            self.message('Give root an empty password')
            self.delete_password(rootdir, 'root')

    def create_users(self, rootdir):
        def create_user(user):
            self.runcmd(['chroot', rootdir, 'adduser', '--gecos', user,
                         '--disabled-password', user])
            if self.settings['sudo']:
                self.runcmd(['chroot', rootdir, 'adduser', user, 'sudo'])

        for userpass in self.settings['user']:
            if '/' in userpass:
                user, password = userpass.split('/', 1)
                create_user(user)
                self.set_password(rootdir, user, password)
            else:
                create_user(userpass)
                self.delete_password(rootdir, userpass)

    def set_password(self, rootdir, user, password):
        encrypted = crypt.crypt(password, '..')
        self.runcmd(['chroot', rootdir, 'usermod', '-p', encrypted, user])

    def delete_password(self, rootdir, user):
        self.runcmd(['chroot', rootdir, 'passwd', '-d', user])

    def remove_udev_persistent_rules(self, rootdir):
        self.message('Removing udev persistent cd and net rules')
        for x in ['70-persistent-cd.rules', '70-persistent-net.rules']:
            pathname = os.path.join(rootdir, 'etc', 'udev', 'rules.d', x)
            if os.path.exists(pathname):
                logging.debug('rm %s' % pathname)
                os.remove(pathname)
            else:
                logging.debug('not removing non-existent %s' % pathname)

    def setup_networking(self, rootdir):
        self.message('Setting up networking')

        f = open(os.path.join(rootdir, 'etc', 'network', 'interfaces'), 'w')
        f.write('auto lo\n')
        f.write('iface lo inet loopback\n')

        if self.settings['enable-dhcp']:
            f.write('\n')
            f.write('auto eth0\n')
            f.write('iface eth0 inet dhcp\n')

        f.close()

    def append_serial_console(self, rootdir):
        if self.settings['serial-console']:
            serial_command = self.settings['serial-console-command']
            logging.debug('adding getty to serial console')
            inittab = os.path.join(rootdir, 'etc/inittab')
            with open(inittab, 'a') as f:
                f.write('\nS0:23:respawn:%s\n' % serial_command)

    def install_grub2(self, rootdev, rootdir):
        self.message("Configuring grub2")
        # rely on kpartx using consistent naming to map loop0p1 to loop0
        install_dev = os.path.join('/dev', os.path.basename(rootdev)[:-2])
        self.runcmd(['mount', '/dev', '-t', 'devfs', '-obind',
                    '%s' % os.path.join(rootdir, 'dev')])
        self.runcmd(['mount', '/proc', '-t', 'proc', '-obind',
                    '%s' % os.path.join(rootdir, 'proc')])
        self.runcmd(['mount', '/sys', '-t', 'sysfs', '-obind',
                    '%s' % os.path.join(rootdir, 'sys')])
        try:
            self.runcmd(['chroot', rootdir, 'update-grub'])
            self.runcmd(['chroot', rootdir, 'grub-install', install_dev])
        except cliapp.AppException as e:
            self.message("Failed. Is grub2-common installed? Using extlinux.")
        self.runcmd(['umount', os.path.join(rootdir, 'sys')])
        self.runcmd(['umount', os.path.join(rootdir, 'proc')])
        self.runcmd(['umount', os.path.join(rootdir, 'dev')])
        self.install_extlinux(rootdev, rootdir)

    def install_extlinux(self, rootdev, rootdir):
        if not os.path.exists("/usr/bin/extlinux"):
            self.message("extlinux not installed, skipping.")
            return
        self.message('Installing extlinux')

        def find(pattern):
            dirname = os.path.join(rootdir, 'boot')
            basenames = os.listdir(dirname)
            logging.debug('find: %s' % basenames)
            for basename in basenames:
                if re.search(pattern, basename):
                    return os.path.join('boot', basename)
            raise cliapp.AppException('Cannot find match: %s' % pattern)

        try:
            kernel_image = find('vmlinuz-.*')
            initrd_image = find('initrd.img-.*')
        except cliapp.AppException as e:
            self.message("Unable to find kernel. Not installing extlinux.")
            logging.debug("No kernel found. %s. Skipping install of extlinux." % e)
            return

        out = self.runcmd(['blkid', '-c', '/dev/null', '-o', 'value',
                           '-s', 'UUID', rootdev])
        uuid = out.splitlines()[0].strip()

        conf = os.path.join(rootdir, 'extlinux.conf')
        logging.debug('configure extlinux %s' % conf)
        kserial = 'console=ttyS0,115200' if self.settings['serial-console'] else ''
        extserial = 'serial 0 115200' if self.settings['serial-console'] else ''
        msg = '''
default linux
timeout 1

label linux
kernel %(kernel)s
append initrd=%(initrd)s root=UUID=%(uuid)s ro %(kserial)s
%(extserial)s
''' % {
            'kernel': kernel_image,
            'initrd': initrd_image,
            'uuid': uuid,
            'kserial': kserial,
            'extserial': extserial,
        }
        logging.debug("extlinux config:\n%s", msg)

        # python multiline string substitution is just ugly.
        # use an external file or live with the mangling, no point in
        # mangling the string to remove spaces just to keep it pretty in source.
        f = open(conf, 'w')
        f.write(msg)
        f.close()

        self.runcmd(['extlinux', '--install', rootdir])
        self.runcmd(['sync'])
        time.sleep(2)

    def optimize_image(self, rootdir):
        """
        Filing up the image with zeros will increase its compression rate
        """
        if not self.settings['sparse']:
            zeros = os.path.join(rootdir, 'ZEROS')
            self.runcmd_unchecked(['dd', 'if=/dev/zero', 'of=' + zeros, 'bs=1M'])
            self.runcmd(['rm', '-f', zeros])

    def squash(self):
        """
        Run squashfs on the image.
        """
        if not os.path.exists('/usr/bin/mksquashfs'):
            logging.warning("Squash selected but mksquashfs not found!")
            return
        self.message("Running mksquashfs")
        suffixed = "%s.squashfs" % self.settings['image']
        self.runcmd(['mksquashfs', self.settings['image'],
                     suffixed,
                     '-no-progress', '-comp', 'xz'], ignore_fail=False)
        os.unlink(self.settings['image'])
        self.settings['image'] = suffixed

    def cleanup_system(self):
        # Clean up after any errors.

        self.message('Cleaning up')

        # Umount in the reverse mount order
        if self.settings['image']:
            for i in xrange(len(self.mount_points) - 1, -1, -1):
                mount_point = self.mount_points[i]
                try:
                    self.runcmd(['umount', mount_point], ignore_fail=False)
                except cliapp.AppException:
                    logging.debug("umount failed, sleeping and trying again")
                    time.sleep(5)
                    self.runcmd(['umount', mount_point], ignore_fail=False)

            self.runcmd(['kpartx', '-d', self.settings['image']], ignore_fail=True)

        for dirname in self.remove_dirs:
            shutil.rmtree(dirname)

    def customize(self, rootdir):
        script = self.settings['customize']
        if not script:
            return
        if not os.path.exists(script):
            example = os.path.join("/usr/share/vmdebootstrap/examples/", script)
            if not os.path.exists(example):
                self.message("Unable to find %s" % script)
                return
            script = example
        self.message('Running customize script %s' % script)
        with open('/dev/tty', 'w') as tty:
            cliapp.runcmd([script, rootdir], stdout=tty, stderr=tty)

    def create_tarball(self, rootdir):
        # Create a tarball of the disk's contents
        # shell out to runcmd since it more easily handles rootdir
        self.message('Creating tarball of disk contents')
        self.runcmd(['tar', '-cf', self.settings['tarball'], '-C', rootdir, '.'])

    def chown(self, rootdir):
        # Change image owner after completed build
        self.message("Changing owner to %s" % self.settings["owner"])
        subprocess.call(["chown",
                         self.settings["owner"],
                         self.settings["image"]])

    def configure_apt(self, rootdir):
        # use the distribution and mirror to create an apt source
        self.message("Configuring apt to use distribution and mirror")
        conf = os.path.join(rootdir, 'etc', 'apt', 'sources.list.d', 'base.list')
        logging.debug('configure apt %s' % conf)
        f = open(conf, 'w')
        f.write('''
deb %(mirror)s %(distribution)s main
#deb-src %(mirror)s %(distribution)s main
''' % {
            'mirror': self.settings['mirror'],
            'distribution': self.settings['distribution']
        })
        f.close()

if __name__ == '__main__':
    VmDebootstrap(version=__version__).run()

