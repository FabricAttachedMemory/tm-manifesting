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
from tm_librarian.tmconfig import TMConfig


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
        self.images_dir = manconfig['TFTP_IMAGES']
        self.grub_dir = manconfig['TFTP_GRUB']
        self.grub_cfg = self.grub_dir + '/grub.cfg'
        self.grub_menu_dir = self.grub_dir + '/menus'
        make_dir(self.grub_menu_dir)
        # Relative to TFTP, these supply content to the files.
        root = manconfig['TFTP_ROOT']
        self.tftp_images_dir = basepath(self.images_dir, root)
        self.tftp_grub_dir = basepath(self.grub_dir, root)
        self.tftp_menu_dir = self.tftp_grub_dir + '/menus'

    @property
    def hostnames(self):
        return ('node%02d' % n for n in range(1, 41))   # generator

    def create_environment(self):
        """
            Create tftp environment: create grub config files based off
        nodes coords, but use only "enclosure and node" values of it.
        These files are static over the lifetime of a machine instance. Then
        create filesystem image directories per these coords for PXE boot
        to pick up on boot .cpio and .vmlinuz.  manifest_api will populate
        those directries when nodes are bound.
        """

        for hostname in self.hostnames:
            # Stays empty until manifest_api does a node binding
            tftp_node_fs = self.images_dir + '/' + hostname
            make_dir(tftp_node_fs)

        for grub_menu_file, img_dir in self.environment.items():
            # each (tftp)/images/* folder and (tftp)/boot/grub/menu.hostname

            grub_menu_content = self.grub_menu_template(hostname)

            with open(grub_menu_file, 'w') as file_obj:
                file_obj.write(str(grub_menu_content))

        grub_cfg_content = self.grub_cfg_template()

        with open(self.grub_cfg, 'w') as file_obj:
            file_obj.write(grub_cfg_content)

    @property
    def environment(self):
        """
            Return dictionary of EFI config path and its filesystem image
        location (under tftp).  Note: path is absolute in EFI space.
        """
        env = {}
        for hostname in self.hostnames:
            grub_menu_file = '%s/%s' % (self.grub_menu_dir, hostname)
            node_dir = '%s/%s/' % (self.tftp_images_dir, hostname)
            env[os.path.normpath(grub_menu_file)] = os.path.normpath(node_dir)
        return env

    def grub_menu_template(self, hostname):
        """
            Return grub.cfg config template that contains .format anchors:
        {node_name} - name of the node
        {node_fs} - TFTP-relative path to the node's filesystem image
                    .cpio and .vmlinuz.
        """
        tftp_dir = '%s/%s' % (self.tftp_images_dir, hostname)
        template = """set default=0
set menu_color_highlight=white/brown

menuentry '{hostname} L4TM ARM64'
  linux (tftp){tftp_dir}/l4tm.vmlinuz
  append root=/dev/ram0 console=ttyAMA0 acpi=force rw
  initrd (tftp){tftp_dir}/l4tm.cpio
"""
        return template.format(hostname=hostname, tftp_dir=tftp_dir)

    def grub_cfg_template(self):
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

        configfile = '%s/${net_default_hostname}' % (self.grub_menu_dir)
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
    env = grubby.environment
    for menu in sorted(env.keys()):
        print('Menu:  %s\nFiles: %s\n' % (menu, env[menu]))
    print('Master GRUB config in', grubby.grub_cfg)


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
