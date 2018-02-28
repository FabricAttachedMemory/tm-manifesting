#!/usr/bin/python3 -tt
"""
    Test cleanup_kernel function of customize_node.py script.
"""
from pdb import set_trace
from argparse import Namespace
import glob
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
        args = {'build_dir' : self.tmp_folder,
                'new_fs_dir' : self.fs_img,
                'dryrun' : True,
                'debug': False}

        args = Namespace(**args)

        init_files = glob.glob(self.fs_img + '/boot/init*')
        vmlinuz_files = glob.glob(self.fs_img + '/boot/vmlinuz*')
        boot_files = init_files + vmlinuz_files
        boot_files = [os.path.basename(basename) for basename in boot_files]

        CN.extract_bootfiles(args)
        # FIXME: Hardcoded names need to be matched to config.py

        for boot_file in boot_files:
            # set_trace()   # doesn't work from test_all.sh, run this directly
            boot_old = '%s/boot/%s' % (self.fs_img, boot_file)
            boot_new = '%s/%s' % (self.tmp_folder, boot_file)
            self.assertFalse(os.path.exists(boot_old),
                    '"%s" should have been removed!' % (boot_old))
            self.assertTrue(os.path.exists(boot_new),
                            '"%s" was not found!' % (boot_new))


if __name__ == '__main__':
    unittest.main()
