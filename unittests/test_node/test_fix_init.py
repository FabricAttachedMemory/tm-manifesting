#!/usr/bin/python3 -tt
"""
"""
from pdb import set_trace

import os
import sys
import unittest
from shutil import rmtree, copytree

import suite_config as config
from pdb import set_trace


class ManifestTest(unittest.TestCase):

    tmcmd = None

    @classmethod
    def setUp(cls):
        set_trace()
        cls.tmcmd = config.tmcmd.tmmanifest
        return


    @classmethod
    def tearDown(cls):
        return


    def test_upload(self):
        """
        """
        set_trace()
        self.assertTrue(False, 'Not Implemented')


if __name__ == '__main__':
    unittest.main()
