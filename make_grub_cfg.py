#!/usr/bin/python3 -tt
"""
    Create TFTP environment for nodes to pick up its curstom FS images.
Each node must have its on grub menu (config) and its own location on TFTP server
for .cpio and .vmlinux files to pickup. This script creates all neccessery files
and folders for TFTP to server for nodes.
"""
import argparse
import os
from pdb import set_trace
from configs import manifest_config as ManCfg

from tm_librarian.tmconfig import TMConfig


class TMtftp(object):
    """
        Set up and configure TFTP server for Manifesting. Generate grub.cfg file
    and grub menu files for each known node. grub.cfg content is generated for
    each node MAC address to be able to pick up its grub menu file. Grub menu
    file is also generated per each node, but is stored as env#/grub.node# file
    which represent each known node coord. That allows for a started node to
    boot its generated FS image (.cpio and vmlinuz).
        FS image folder is also generate in this class under (tftp)/arm64/enc#/node#/
    folder structure.
        Overall grub dependency:
    grub.cfg ---knows about ---> grub.enc#/grub.node# --picks up cpio--> (tftp)/arm64/enc#/node#/.cpio
    """

    def __init__(self, nodes_cfg):
        """
        :param 'tftp_root': [str] absolute path to the TFTP folder on the server.
        :param 'nodes_cfg': [tm_librarian.tmconfig] parsed hpetmconfig.json file.
        :param 'filesystem_dir': [str] relative to TFTP folder path to saved cpio and vmlinuz files.
        """
        self.root = ManCfg.TFTP_ROOT   # absolute path to TFTP on the server.
        assert os.path.isdir(self.root), 'Can\'t find TFTP server at "%s"!' % (self.root)

        self.grub_dir = ManCfg.TFTP_GRUB
        assert os.path.isdir(self.root + '/' + self.grub_dir), 'Couldn\'t find %s!' % (self.grub_dir)

        self.filesystem_dir = ManCfg.TFTP_IMAGES

        self.node_cfg = nodes_cfg
        self.nodes = nodes_cfg.nodes


    def create_environment(self):
        """
            Create tftp environment: create efi config files based of nodes coords,
        but use only "enclosure and node" values of it. Then create filesystem image
        directories per these coords for grab to pick up on boot .cpio and .vmlinuz.
        """
        for efi_cfg in self.environment.keys(): # each folder for (tftp)/arm64/* and (tftp)/boot/grub/enc*/
            grub_folders = os.path.normpath(self.root + '/' + os.path.dirname(efi_cfg))
            make_dir(grub_folders)      # folders for grub files (tftp)/boot/grub/enc#/

            node_fs = self.root + '/' + self.environment[efi_cfg]
            make_dir(node_fs)           # folders for FS images per node. (tftp)/arm64/enc#/node#/

            grub_menu_file = self.root + '/' + efi_cfg
            grub_menu_content = self.grub_menu_template(self.environment[efi_cfg])

            with open(grub_menu_file, 'w') as file_obj:
                file_obj.write(str(grub_menu_content))

        grub_cfg_file = self.root + '/' + self.grub_dir + '/grub.cfg'
        grub_cfg_content = self.grub_cfg_template()

        with open(grub_cfg_file, 'w') as file_obj:
            file_obj.write(grub_cfg_content)


    @property
    def environment(self):
        """
            Return dictionary of nodes' efi config path relative to tftp root and
        its filesystem image location (on tftp).
        Example: { 'boot/grub/enc#/grub.node#' : 'arm64/enc#/node#/' }
        Note: path is relative to TFTP!
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


def main(args):
    """
        Configure TFTP environment.
    """
    tmconfig = TMConfig(args['config'])
    #tftp_root = os.path.normpath(manifest_config.MANIFESTING_ROOT + '/tftp/')

    TFTP = TMtftp(tmconfig)
    TFTP.create_environment()


if __name__ == '__main__':
    """ Parse command line arguments. """
    parser = argparse.ArgumentParser(description='TODO')
    parser.add_argument('--config',
                        help='Nodes coords config json.',
                        default='configs/hpetmconfig.json')

    args, _ = parser.parse_known_args()
    main(vars(args))
