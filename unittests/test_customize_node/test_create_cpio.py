#!/usr/bin/python3 -tt
"""
    Test create_cpio function of customize_node.py script.
"""
from pdb import set_trace

import os
import sys
import unittest
from shutil import rmtree, copytree

import config
from config import CN


class CreateCpioTest(unittest.TestCase):

    tmp_folder = "/tmp/UNITTEST_CUSTOMNODE/"
    fs_img = "/tmp/UNITTEST_CUSTOMNODE/fs_img/"

    @classmethod
    def setUp(cls):
        """
            Emulare a filesystem image in the tmp directory with only those folders
        and files that are manipulated by customize_node.py script.
        """
        config.setup()
        cls.tmp_folder = config.tmp_folder
        cls.fs_img = config.fs_img


    @classmethod
    def tearDown(cls):
        if os.path.isdir(cls.tmp_folder):
            rmtree(cls.tmp_folder)


    def test_create_cpio(self):
        """
        """
        cpio_file = '%s/fs_img.cpio' % self.tmp_folder
        CN.create_cpio(cpio_file, self.fs_img)
        self.assertTrue(os.path.exists(cpio_file), 'cpio file was not created!')


    #TODO: Test exceptions!


if __name__ == '__main__':
    unittest.main()
