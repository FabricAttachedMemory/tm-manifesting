#!/usr/bin/python3 -tt
"""
    Test customize_node.py script.
"""
from pdb import set_trace

import os
import tempfile
import unittest
from shutil import rmtree, copytree

from tmms.utils import utils


class UtilsTest(unittest.TestCase):

    @classmethod
    def setUp(cls):
        pass


    @classmethod
    def tearDown(cls):
        pass


    def test_parse_vmd(self):
        ''' '''
        vmd_path = os.path.realpath('./mock/test.vmd')

        vmd_data = utils.parse_vmd(vmd_path)
        self.assertTrue(vmd_data != {})
        self.assertTrue('arch' in vmd_data)
        self.assertTrue(vmd_data['arch'] == 'amd64')


if __name__ == '__main__':
    unittest.main()
