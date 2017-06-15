#!/usr/bin/python3
"""
    Set of tests for for tmcmd/tm_package.py of the API.
"""
import json
import os
import unittest
from pdb import set_trace

from tmms.configs.build_config import ManifestingConfiguration as MC


class PackageTest(unittest.TestCase):

    tmms_path = './mock/tmms'
    expected_values = {
        'TMCONFIG' : './tmconfig',
        'HOST' : '0.0.0.0',
        'PORT' : 31178,
        'MANIFESTING_ROOT' : '/tmp/tmms-test',
        'TFTP_ROOT' : '/tmp/tmms-test/tftp',
        'L4TM_MIRROR' : 'http://hlinux-deejay.us.rdlabs.hpecorp.net/l4tm-pushed',
        'L4TM_RELEASE' : 'catapult',
        'L4TM_AREAS' : ('main', 'contrib', 'non-free' ),
        'PXE_INTERFACE' : None,
        'PXE_FIREWALL' : 'DHCP',
        'PXE_SUBNET' : None
        }

    @classmethod
    def setUpClass(cls):
        pass


    def test_init(self):
        cfg= MC(self.tmms_path, False)
        try:
            MC(self.tmms_path)
            self.assertTrue(False, 'Failed to catch missing folders!')
        except ValueError:
            self.assertTrue(True)


    def test_keys(self):
        cfg= MC(self.tmms_path, False)
        keys = cfg.keys()

        # Verify all the keys and values from the tmms config file are parsed
        # into config object by ManifestingConfiguration.
        for expected_key, expected_val in self.expected_values.items():
            self.assertTrue(expected_key in keys,
                        'Expected key [%s] is not in config keys!' % expected_key)
            self.assertTrue(expected_val == cfg[expected_key],
                        'Expected value [%s : %s] doesnt match [%s]!' % \
                        (expected_key, expected_val, cfg[expected_key]))
        self.assertIsNone(cfg['DOES_NOT_EXIST'])


if __name__ == '__main__':
    unittest.main()
