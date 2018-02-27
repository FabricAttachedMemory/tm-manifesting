#!/usr/bin/python3 -tt
"""
    Test set_hostname function of customize_node.py script.
"""
from pdb import set_trace
from argparse import Namespace
import os
import sys
import unittest
from shutil import rmtree, copytree

import config
from config import CN


class CustomizeNodeRoutineTest(unittest.TestCase):

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

    def test_set_hostname(self):
        """
            Assume there is a mock filesystem image already created. Thus, try
        to set a custom name to etc/hostname using customize_node.set_hostname
        function.
        """
        hostname_test = 'Abyss'
        hostname_file = '%s/etc/hostname' % self.fs_img
        args = {'new_fs_dir' : self.fs_img,
                'hostname' : hostname_test,
                'dryrun' : True}
        args = Namespace(**args)

        CN.set_hostname(args)
        hostname_new = None
        with open(hostname_file, 'r') as file_obj:
            hostname_new = file_obj.read()
        self.assertTrue(hostname_test in hostname_new,
                'Hostname was not set to "%s"!' % hostname_test)


if __name__ == '__main__':
    unittest.main()
