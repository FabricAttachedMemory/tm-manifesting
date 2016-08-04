#!/usr/bin/python3 -tt
"""
    Test cleanup_kernel function of customize_node.py script.
"""
from pdb import set_trace

import os
import sys
import unittest
from shutil import rmtree, copytree

import config
from config import CN


class CleanupKernelTest(unittest.TestCase):

    tmp_folder = "/tmp/UNITTEST_CUSTOMNODE/FIXME/OVERWRITTEN/BELOW"
    fs_img = "/tmp/UNITTEST_CUSTOMNODE/fs_img/FIXME/OVERWRITTEN_BELOW"

    @classmethod
    def setUp(cls):
        """
            Emulate a filesystem image in the tmp directory with only those
        folders and files that are manipulated by customize_node.py script.
        """
        config.setup()
        cls.tmp_folder = config.tmp_folder          # FIXME: OVERWRITES ABOVE
        cls.fs_img = config.fs_img


    @classmethod
    def tearDown(cls):
        if os.path.isdir(cls.tmp_folder):
            rmtree(cls.tmp_folder)


    def test_cleanout_kernel(self):
        """
            Assume there is a mock filesystem image already created.
        Try to move boot/ files into tmp directory using
        customize_node.cleanout_kernel function.
        """
        CN.cleanout_kernel(self.tmp_folder, self.fs_img)
        # FIXME: Hardcoded names need to be matched to config.py
        boot_files = ['initrd.img-4.5.0-3-arm64-l4tm-tmas',
                         'vmlinuz-4.5.0-3-arm64-l4tm-tmas']
        for boot_file in boot_files:
            # set_trace()   # doesn't work from test_all.sh, run this directly
            boot_old = '%s/boot/%s' % (self.fs_img, boot_file)
            boot_new = '%s/%s' % (self.tmp_folder, boot_file)
            self.assertFalse(os.path.exists(boot_old),
                    '"%s" should have been removed!' % (boot_old))
            self.assertTrue(os.path.exists(boot_new),
                            '"%s" was not found!' % (boot_new))


    def test_cleanout_kernel_exception(self):
        """
            Assume there is a mock filesystem image already created.  Try
        to move boot/ files into tmp directory using
        customize_node.cleanout_kernel function. In this test we are trying
        to catch an error, thus the boot files will not exist, so that the
        RuntimeError will be thrown.
        """
        boot_dir = '%s/boot/' % self.fs_img
        rmtree(boot_dir)
        self.assertFalse(os.path.isdir(boot_dir), 'Couldn\'t remove boot/!')

        self.assertRaises(RuntimeError,
            CN.cleanout_kernel(self.tmp_folder, self.fs_img),
            'Unexpected error was raised!')


    #TODO: test exceptions!

if __name__ == '__main__':
    unittest.main()
