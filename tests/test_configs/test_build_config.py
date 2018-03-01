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

    expected_values = {
        'TMCONFIG' : './tmconfig',
        'HOST' : '0.0.0.0',
        'PORT' : 31178,
        'MANIFESTING_ROOT' : '/tmp/tmms-test',
        'TFTP_ROOT' : '/tmp/tmms-test/tftp',
        'DEBIAN_MIRROR' : 'http://seedy.us.rdlabs.hpecorp.net/Debian',
        'DEBIAN_RELEASE' : 'jessie',
        'DEBIAN_AREAS' : ('main', 'contrib', 'non-free' ),
        'PXE_INTERFACE' : None,
        'PXE_FIREWALL' : 'DHCP',
        'PXE_SUBNET' : None
        }

    @classmethod
    def setUpClass(cls):
        this_file_abs = os.path.abspath(__file__)
        this_file_dir = os.path.dirname(this_file_abs)
        cls.tmms_path = this_file_dir + '/mock/tmms'


    def test_init(self):
        cfg = MC(self.tmms_path, False)
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
