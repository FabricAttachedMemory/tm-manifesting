#!/usr/bin/python3 -tt
"""
"""
from pdb import set_trace

import glob
import os
import sys
import unittest
from shutil import rmtree, copytree

import suite_config as config
from pdb import set_trace

MANIFEST_UPLOADS = config.server_config.MANIFESTING_ROOT + '/manifest_uploads/'

class ManifestTest(unittest.TestCase):

    tmcmd = None
    backup_folder = '/tmp/manifest_api_test/'

    @classmethod
    def setUp(cls):
        cls.tmcmd = config.tmcmd.tmmanifest
        return


    @classmethod
    def tearDown(cls):
        return


    def testUploadNoPrefix(self):
        """
        """
        self.tmcmd.upload(['', './mock-data/manifest.test'])
        self.assertTrue(False, 'Not Implemented')


if __name__ == '__main__':
    unittest.main()
