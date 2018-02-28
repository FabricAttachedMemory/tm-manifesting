#!/usr/bin/python3 -tt
"""
    Test create_cpio function of customize_node.py script.
"""
from pdb import set_trace
from argparse import Namespace
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
            Test create_cpio func of customize_imga.py script.
        Validate a .cpio file is created in expected location with a provided
        hostname for the node.
        """
        hostname = 'unittest_host'
        cpio_file = '%s/%s.cpio' % (self.tmp_folder, hostname)
        args = {'new_fs_dir' : self.fs_img,
                'dest_file' : cpio_file,
                'hostname' : hostname,
                'build_dir' : self.tmp_folder,
                'verbose' : False,
                'dryrun' : True}
        args = Namespace(**args)

        CN.create_cpio(args)

        self.assertTrue(os.path.exists(cpio_file), 'cpio file was not created!')


if __name__ == '__main__':
    unittest.main()
