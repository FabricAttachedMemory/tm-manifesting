#!/usr/bin/python3 -tt
"""
    Create TFTP environment for nodes to pick up custom FS images.
Each node must have its on grub menu, kernel (vmlinuz), and FS image (cpio)
under the TFTP server.  This script generates the grub menu files plus
a single master grub.cfg which is originally downloaded by grub.efi.

    Details: A node boots and system firmware (SFW) downloads (via TFTP)
a single file, the bootloader which is grub.efi.  Grub turns around and
grabs its master grub.cfg file.  All nodes will use this same grub.cfg.
grub.cfg content is based on the DHCP "ClientID" option, as opposed to
the traditional MAC address.  The ClientID contains the node's physical
location (enclosure and node number).  This is evaluated by grub to
choose a specific "menu" file.  Grub menu file is generated per each
node and is stored as env#/grub.node# file which represent each known
node coord. That menu specifies the precise kernel file (vmlinuz) and
customized FS image (.cpio file).
"""

import argparse
import os
import sys

from pdb import set_trace

from configs.build_config import ManifestingConfiguration
from utils.utils import make_dir, basepath


class TMgrub(object):
    """
        Generate all grub grub config files under the TFTP hierarchy.
        At "tftp" element of hierarchy (default /var/lib/tmms/tftp):
        - boot/
          grub.cfg
          - menus/
            nodeXX.menu (menu files)
        -images/
          - nodeXX/ (directories)
            nodeXX.vmlinuz and nodeXX.cpio
    """

    def __init__(self, manconfig):
        """
        :param 'manfconfig': dictionary with many ratified file paths
        """

        # Absolute paths are for writing files.  _tftp_xxxx are file contents.
        self.tftp_images_dir = manconfig['TFTP_IMAGES']
        self.tftp_grub_dir = manconfig['TFTP_GRUB']
        self.tftp_grub_menus_dir = self.tftp_grub_dir + '/menus'
        make_dir(self.tftp_grub_menus_dir)

        self.dnsmasq_dir = manconfig['DNSMASQ_CONFIGS']

        # Relative to TFTP, these supply content to the files.
        root = manconfig['TFTP_ROOT']
        self.chroot_images_dir = basepath(self.tftp_images_dir, root)
        self.chroot_grub_dir = basepath(self.tftp_grub_dir, root)
        self.chroot_grub_menus_dir = self.chroot_grub_dir + '/menus'

        # Last but not least, the master grub config file loaded by grub
        self.tftp_grub_cfg = self.tftp_grub_dir + '/grub.cfg'

    @property
    def hostnames(self):
        return ('node%02d' % n for n in range(1, 41))   # generator

    def configure_dnsmasq(self):
        '''Plagiarized from a libvirt setup'''

        with open(self.dnsmasq_dir + '/tmms.addnhosts', 'w') as f:
            f.write('10.11.10.254	torms')

        with open(self.dnsmasq_dir + '/tmms.conf', 'w') as f:
            for line in '''
                strict-order
                domain=have.it.your.way
                expand-hosts
                pid-file=/var/run/tmms_dnsmasq.pid
                except-interface=lo
                bind-dynamic
                interface=net_accessP
                srv-host=_librarian._tcp,torms,9093
                dhcp-range=10.11.10.254,static
                dhcp-no-override
                enable-tftp
                tftp-root=/var/lib/tmms/tftp/
                dhcp-boot=/boot/bootaarch64.efi
                dhcp-hostsfile=/var/lib/tmms/dnsmasq/tmms.hostsfile
                addn-hosts=/var/lib/tmms/dnsmasq/tmms.addnhosts
            '''.split('\n'):
                f.write(line.strip() + '\n')

        with open(self.dnsmasq_dir + '/tmms.hostsfile', 'w') as f:
            for i, hostname in enumerate(self.hostnames):
                physloc = 'enclosure/%d/node/%d' % (
                    (i // 10) + 1,
                    (i % 10) + 1)
                ip = '10.11.10.%d' % (i + 1)
                f.write('id:%s,%s,%s\n' % (physloc, ip, hostname))

    def create_environment(self):
        """
            Create tftp environment: grub menu files based off
        node's hostname, which is implicitly the node's physical location.
        These files are static over the lifetime of a machine instance. Then
        create filesystem image directories per these coords for PXE boot
        to pick up on boot .cpio and .vmlinuz.  manifest_api will populate
        those directories when nodes are bound.
        """

        grub_cfg_content = self.grub_cfg_compose()
        with open(self.tftp_grub_cfg, 'w') as file_obj:
            file_obj.write(grub_cfg_content)

        for hostname in self.hostnames:
            tftp_node_fs = self.tftp_images_dir + '/' + hostname
            make_dir(tftp_node_fs)
            grub_menu_content = self.grub_menu_compose(hostname)
            menu_fname = '%s/%s.menu' % (self.tftp_grub_menus_dir, hostname)
            with open(menu_fname, 'w') as file_obj:
                file_obj.write(str(grub_menu_content))

        self.configure_dnsmasq()

    def grub_menu_compose(self, hostname):
        """
            Return grub menu content that contains .format anchors:
        {node_name} - name of the node
        {node_fs} - TFTP-relative path to the node's filesystem image
                    .cpio and .vmlinuz.
        """
        tftp_dir = '%s/%s' % (self.chroot_images_dir, hostname)
        template = """set default=0
set menu_color_highlight=white/brown

menuentry '{hostname} L4TM ARM64'
  linux (tftp){tftp_dir}/l4tm.vmlinuz
  append root=/dev/ram0 console=ttyAMA0 acpi=force rw
  initrd (tftp){tftp_dir}/l4tm.cpio
"""
        return template.format(hostname=hostname, tftp_dir=tftp_dir)

    def grub_cfg_compose(self):
        """
            Template string for a grub.cfg that references grub menu
        for each node on PXE boot.
        """
        header_tplt = """set gfxmode=auto
insmod efi_gop
insmod efi_uga
insmod gfxterm
terminal_output gfxterm
"""

        lines = header_tplt.split('\n')

        configfile = '%s/${net_default_hostname}' % (self.chroot_grub_menus_dir)
        lines.append('configfile "(tftp)%s' % configfile)

        return '\n'.join(lines)


def main(config_file):
    """
        Configure TFTP environment.
    """

    manconfig = ManifestingConfiguration(config_file, autoratify=False)
    missing = manconfig.ratify(dontcare=('GOLDEN_IMAGE', 'TMCONFIG'))
    if missing:
        raise RuntimeError('\n'.join(missing))
    grubby = TMgrub(manconfig)
    grubby.create_environment()
    print('Master GRUB configuration in', grubby.tftp_grub_cfg)
    print('      Per-node grub menus in', grubby.tftp_grub_menus_dir)
    print('      Per-node image dirs in', grubby.tftp_images_dir)
    print('             dnsmasq.conf in', grubby.dnsmasq_dir)


if __name__ == '__main__':
    """ Parse command line arguments. """
    parser = argparse.ArgumentParser(description='Generate GRUB2 config files')
    parser.add_argument('--config',
                        help='Manifest API server configuration file',
                        default='manifest_config.py')
    args, _ = parser.parse_known_args(sys.argv[1:])

    msg = 0     # establish scope
    try:
        main(args.config)
    except Exception as e:
        msg = str(e)
    raise SystemExit(msg)
