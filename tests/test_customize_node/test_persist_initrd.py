#!/usr/bin/python3 -tt
"""
    Test fix_init function of customize_node.py script.
"""
from pdb import set_trace
from argparse import Namespace
import os
import sys
import unittest
from shutil import rmtree, copytree

import config
from config import CN


class FixInitTest(unittest.TestCase):

    tmp_folder = "/tmp/UNITTEST_CUSTOMNODE/"
    fs_img = "/tmp/UNITTEST_CUSTOMNODE/fs_img/"

    @classmethod
    def setUp(cls):
        """
            Emulate a filesystem image in the tmp directory with only those
        folders and files that are manipulated by customize_node.py script.
        """
        config.setup()
        cls.tmp_folder = config.tmp_folder
        cls.fs_img = config.fs_img


    @classmethod
    def tearDown(cls):
        if os.path.isdir(cls.tmp_folder):
            rmtree(cls.tmp_folder)

    def test_fix_init(self):
        """
            Assume there is a mock filesystem image already created. Thus, try
        to create a symbolic link from fs_img/sbin/init into fs_img/init.
        """
        args = {'new_fs_dir' : self.fs_img,
                'dryrun' : True}
        args = Namespace(**args)

        CN.persist_initrd(args)
        new_init = '%s/init' % self.fs_img

        self.assertTrue(os.path.exists(new_init),
                'Symlink to "%s" was not created!' % new_init)

        CN.persist_initrd(args)
        self.assertTrue(os.path.exists(new_init),
                'Recreating symlink to "%s" faild! Couldn\'t remove old init!' % new_init)


    def test_fix_init_exception(self):
        """
            Assume there is a mock filesystem image already created. Thus, try
        to create a symbolic link from fs_img/sbin/init into fs_img/init. This
        time, we will try to catch a RuntimeError exception, by removing init
        file before creating a symlink.
        """
        orig_init = '%s/sbin/init' % self.fs_img
        os.remove(orig_init)
        args = {'new_fs_dir' : self.fs_img,
                'dryrun' : True}
        args = Namespace(**args)

        try:
            CN.persist_initrd(args)
            self.assertTrue(False, ms='No RuntimeError for fix_init with incorrect env.')
        except RuntimeError:
            self.assertTrue(True)

        args.new_fs_dir = '/tmp/'
        try:
            CN.persist_initrd(args)
            self.assertTrue(False, 'RuntimeError was not raised for wrong init env.')
        except RuntimeError:
            self.assertTrue(True)


    #TODO: test more exceptions!

if __name__ == '__main__':
    unittest.main()
