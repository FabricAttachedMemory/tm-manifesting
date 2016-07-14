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

from configs.build_config import make_config, ratify_config
from tm_librarian.tmconfig import TMConfig


class TMgrub(object):
    """
        Generate all grub grub config files under the TFTP hierarchy.
        FS image folder is also generated in this class under
    (tftp)/arm64/enc#/node#/ folder structure.
        Overall grub dependency:
    grub.cfg (knows about enc#/node# --> (tftp)/arm64/enc#/node#/kernel & FS
    """

    def __init__(self, manconfig):
        """
        :param 'manfconfig': dictionary with many ratified file paths
        """

        self.root = manconfig['TFTP_ROOT']
        self.grub_dir = manconfig['TFTP_GRUB']
        self.filesystem_dir = manconfig['TFTP_IMAGES']
        self.node_cfg = TMConfig(manconfig['TMCONFIG'])
        self.nodes = self.node_cfg.nodes


    def create_environment(self, verbose=True):
        """
            Create tftp environment: create grub config files based off
        nodes coords, but use only "enclosure and node" values of it.
        These files are static over the lifetime of a machine instance. Then
        create filesystem image directories per these coords for PXE boot
        to pick up on boot .cpio and .vmlinuz.  manifest_api will populate
        those directries when nodes are bound.
        """

        self.verbose = verbose
        for efi_cfg, img_dir in self.environment.items():
            # each (tftp)/images/* folder and (tftp)/boot/grub/menu.hostname
            for node in self.nodes:
                tftp_node_fs = self.filesystem_dir + '/' + node.hostname
                make_dir(tftp_node_fs)

            grub_menu_content = self.grub_menu_template(img_dir)

            with open(efi_cfg, 'w') as file_obj:
                file_obj.write(str(grub_menu_content))

        grub_cfg_file = self.grub_dir + '/grub.cfg'
        grub_cfg_content = self.grub_cfg_template()

        with open(grub_cfg_file, 'w') as file_obj:
            file_obj.write(grub_cfg_content)


    @property
    def environment(self):
        """
            Return dictionary of nodes' efi config path and its filesystem image
        location (on tftp).
        Example: { '(tftp)/boot/grub/menu.hostname' : '(tftp)/images/hostname/' }
        Note: path is absolute.
        """
        env = {}
        for node in self.nodes:
            efi_cfg = '%s/menu.%s' % (self.grub_dir, node.hostname)
            node_dir = '%s/%s/' % (self.filesystem_dir, node.hostname)
            env[os.path.normpath(efi_cfg)] = os.path.normpath(node_dir)
        return env


    @staticmethod
    def grub_menu_template(node_fs):
        """
            Return grub.cfg config template that contains .format anchors:
        {node_name} - name of the node
        {node_fs} - path (relative to TFTP server) to the node's filesystem image
                    .cpio and .vmlinuz on tftp.
        """
        template = """set default=0
set menu_color_highlight=white/brown

menuentry 'L4TM Catapult ARM64(Node: {node_fs})' {{
  linux (tftp){node_fs}/l4tm.vmlinuz --append root=/dev/ram0 console=ttyAMA0 acpi=force rw
  initrd (tftp){node_fs}/l4tm.cpio
}}
fi
"""
        return template.format(node_fs=node_fs)


    def grub_cfg_template(self):
        """
            Template string for a grub.cfg that is responsible for grub menu on
        PXE boot. This code looks at each Node information and establish relationship
        between its MAC address and a grub.{hostname} config file generated for it.
        """
        header_tplt = """set gfxmode=auto
insmod efi_gop
insmod efi_uga
insmod gfxterm
terminal_output gfxterm
"""

        menu_tplt = """
if [ "$net_default_mac" -eq "{mac}" ];then
    configfile "(tftp){menu_cfg}"
fi
"""
        lines = []
        lines.append(header_tplt)

        for node in self.nodes:
            node_mac = node.soc.socMacAddress
            menu_cfg = '%s/menu.%s' % (self.grub_dir, node.hostname)
            lines.append(menu_tplt.format(mac=node_mac, menu_cfg=menu_cfg))

        return '\n'.join(lines)


def make_dir(target):
    """
        Create a directory tree at requested location. Don't do anything if folder
    already exists.

    :param 'target': [str] folder tree to create.
    :return: False - folde laready exists. True - folders created. RuntimeError - couldn't create.
    """
    if os.path.isdir(target):
        return False

    try:
        os.makedirs(target)
    except IOError:
        raise RuntimeError('Couldn\'t create "%s" folder!' % (target))

    return True


def main(config_file):
    """
        Configure TFTP environment.
    """

    manconfig = make_config(config_file)
    missing = ratify_config(manconfig, dontcare=('GOLDEN_IMAGE',))
    if missing:
        raise RuntimeError('\n'.join(missing))
    TFTP = TMgrub(manconfig)
    TFTP.create_environment()
    TFTP.print_status()


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
