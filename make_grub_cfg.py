#!/usr/bin/python3 -tt
"""
    Create TFTP environment for nodes to pick up its curstom FS images.
Each node must have its on grub menu (config) and its own location on TFTP server
for .cpio and .vmlinux files to pickup. This script creates all neccessery files
and folders for TFTP to server for nodes.
"""
import argparse
import os

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

    def __init__(self, nodes_cfg, tftp_root, grub_dir, tftp_imgs):
        """
        :param 'tftp_root': [str] absolute path to the TFTP folder on the server.
        :param 'nodes_cfg': [tm_librarian.tmconfig] parsed hpetmconfig.json file.
        :param 'filesystem_dir': [str] relative to TFTP folder path to saved cpio and vmlinuz files.
        """
        self.root = tftp_root
        assert os.path.isdir(self.root),\
                'Can\'t find TFTP location at "%s"!' % (self.root)

        self.grub_dir = grub_dir
        assert os.path.isdir(self.grub_dir),\
                'Couldn\'t find grub directory at %s!' % (self.grub_dir)

        self.filesystem_dir = tftp_imgs
        assert os.path.isdir(self.filesystem_dir),\
                'Couldn\'t find fs images directory at %s!' % (self.filesystem_dir)

        self.node_cfg = nodes_cfg
        self.nodes = nodes_cfg.nodes


    def create_environment(self):
        """
            Create tftp environment: create efi config files based of nodes coords,
        but use only "enclosure and node" values of it. Then create filesystem image
        directories per these coords for grab to pick up on boot .cpio and .vmlinuz.
        """
        for efi_cfg, img_dir in self.environment.items(): # each (tftp)/images/* folder and (tftp)/boot/grub/menu.hostname file
            for node in self.nodes:
                tftp_node_fs = self.filesystem_dir + '/' + node.hostname
                make_dir(tftp_node_fs)   # folders for FS images per node. (tftp)/images/hostname/

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


def main(args):
    """
        Configure TFTP environment.
    """
    tmconfig = TMConfig(args['tmconfig'])

    TFTP = TMtftp(tmconfig, args['tftp_root'], args['tftp_grub'], args['tftp_images'])
    TFTP.create_environment()


if __name__ == '__main__':
    """ Parse command line arguments. """
    parser = argparse.ArgumentParser(description='TODO')
    parser.add_argument('--tmconfig',
                        help='Nodes coords config json.',
                        default='configs/hpetmconfig.json')
    parser.add_argument('--tftp-root',
                        help='Path to the TFTP server.')
    parser.add_argument('--tftp-grub',
                        help='Path to the TFTP\'s grub folder.')
    parser.add_argument('--tftp-images',
                        help='Path to the TFTP\'s filesystem images folder.')
    args, _ = parser.parse_known_args()
    main(vars(args))
