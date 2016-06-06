#!/usr/bin/python3 -tt
"""
    Create grub configs for each known node mac address.
"""
import argparse
import os
from pdb import set_trace
from configs import manifest_config

from tm_librarian.tmconfig import TMConfig


class TM_TFTP():
    """
        Set up and configure TFTP server for Manifesting.
    """

    def __init__(self, tftp_root, nodes_cfg, filesystem_dir='arm64/'):
        assert os.path.isdir(tftp_root), 'Can\'t find TFTP server at "%s"!' % (tftp_root)
        self.root = tftp_root   # absolute path to TFTP on the server.

        self.grub_dir = '/boot/grub/'
        assert os.path.isdir(self.grub_dir), 'Couldn\'t find %s!' % (self.grub_dir)

        self.filesystem_dir = filesystem_dir

        self.node_cfg = nodes_cfg
        self.nodes = nodes_cfg.nodes
        self.eficonfig_mock = './configs/efidefault.mock'



    def create_environment(self):
        """
            Create tftp environment: create efi config files based of nodes mac;
        create filesystem image directories per node mac.
        """
        for efi_cfg in self.environment.keys():
            grub_file = self.root + '/' + efi_cfg

            set_opt = '\n'.join(['set default=0', 'set menu_color_highlight=white/brown'])
            mac = efi_cfg.split('/grub.')[-1]
            grub_content = self.grub_content(set_opt, mac)

            with open(grub_file, 'w') as file_obj:
                file_obj.write(str(grub_content))

            filesystem_dir = self.root + '/' + self.environment[efi_cfg]
            try:
                os.makedirs(filesystem_dir)
            except IOError:
                raise RuntimeError('Couldn\'t create filesystem boot directories at %s!' % (self.filesystem_dir))


    @property
    def environment(self):
        """
            Return dictionary of nodes' efi config path relative to tftp root and
        its filesystem image location (on tftp).
        Example: { 'boot/grub/grub.01:01:01:01:01:01' : 'arm64/01:01:01:01:01:01' }
        Note: path is relative to TFTP!
        """
        env = {}
        for node in self.nodes:
            mac = node.soc.socMacAddress
            efi_cfg = '%s/grub.%s' % (self.grub_dir, mac)
            node_dir = self.filesystem_dir + '/' + mac
            env[efi_cfg] = os.path.normpath(node_dir)
        return env


    def grub_content(self, set_opt, mac):
        """
            Open efidefault mock file in the configs/ folder and insert passed
        variables to it to complete the file.

        :param 'set_opt': [str] 'set' variables of the grub's efi.config.
        :param 'mac': [str] mac adress of the node to bind config with. (Format: 01:01:01:01:01:01)

        :return: [str] config's content.
        """
        content = None
        with open(self.eficonfig_mock, 'r') as efi_obj:
            content = efi_obj.read()

        content = content.format(set_opt=set_opt,
                            mac=mac,
                            filesystem_dir=self.filesystem_dir)
        return content


def main(args):
    """
        Configure TFTP environment.
    """
    tmconfig = TMConfig(args['config'])
    tftp_root = os.path.normpath(manifest_config.MANIFESTING_ROOT + '/tftp/')

    TFTP = TM_TFTP(tftp_root, tmconfig)
    TFTP.create_environment()


if __name__ == '__main__':
    """
        Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description='TODO')
    parser.add_argument('--config',
                        help='Nodes coords config json.',
                        default='configs/hpetmconfig.json')

    args, _ = parser.parse_known_args()
    main(vars(args))
