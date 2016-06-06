#!/usr/bin/python3 -tt
"""
    Create grub configs for each known node mac address.
"""

import argparse
from pdb import set_trace
from configs import manifest_config

from tm_librarian.tmconfig import TMConfig


def main(args):
    """
        TODO
    """
    tmconfig = TMConfig(args['config'])
    cfg_to_create = []
    for node in tmconfig.nodes:
        file_name = node.soc.socMacAddress.replace(':', '')
        file_name = 'efi.cfg-' + file_name
        cfg_to_create.append(file_name)
    set_trace()




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='TODO')
    parser.add_argument('--config',
                        help='Nodes coords config json.',
                        default='configs/hpetmconfig.json')

    args, _ = parser.parse_known_args()
    main(vars(args))
