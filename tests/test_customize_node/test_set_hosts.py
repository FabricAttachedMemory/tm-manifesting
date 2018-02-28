#!/usr/bin/python3 -tt
"""
    Test set_hosts function of customize_node.py script.
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


    def test_set_hosts(self):
        """
            Assume there is a mock filesystem image already created. Thus, try
        """
        hosts_file = '%s/etc/hosts' % self.fs_img
        hostname = 'Abyss'
        args = {'new_fs_dir' : self.fs_img,
                'hostname' : hostname,
                'dryrun' : True }
        args = Namespace(**args)

        CN.set_hosts(args)

        hosts_new = None
        with open(hosts_file, 'r') as file_obj:
            hosts_new = file_obj.read()

        localhost_line = '127.0.0.1   localhost'
        hostname_line = '127.1.0.1   %s' % hostname
        self.assertTrue(localhost_line in hosts_new, '"%s" is not in etc/hosts!' % localhost_line)
        self.assertTrue(hostname_line in hosts_new, '"%s" is not in etc/hosts!' % hostname_line)


if __name__ == '__main__':
    unittest.main()
