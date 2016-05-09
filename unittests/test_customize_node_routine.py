#!/usr/bin/python3 -tt
"""
    Test set of functions that are responsible for filesystem image customization,
e.g. kernel cleanup, fixing init and etc.
"""
from pdb import set_trace

import os
import shlex
import sys
import unittest
from shutil import rmtree, copytree
customize_node = os.path.realpath(__file__)
customize_node = os.path.dirname(customize_node)
customize_node = '%s/../blueprints/30-nodes/node_builder/' % (customize_node)
sys.path.append(customize_node)
import customize_node as CN


class CustomizeNodeRoutineTest(unittest.TestCase):

    tmp_folder = "/tmp/UNITTEST_CUSTOMNODE/"
    fs_img = "/tmp/UNITTEST_CUSTOMNODE/fs_img/"

    @classmethod
    def setUp(cls):
        """
            Emulare a filesystem image in the tmp directory with only those folders
        and files that are manipulated by customize_node.py script.
        """
        if os.path.isdir(cls.tmp_folder):
            rmtree(cls.tmp_folder)
        if os.path.isdir(cls.fs_img):
            rmtree(cls.fs_img)
        os.makedirs(cls.tmp_folder)
        os.makedirs(cls.fs_img)

        fs_dirtree = ['boot/', 'etc/', 'etc/apt/sources.list.d/']
        fs_files = ['boot/initrd.img-4.3.0-3-arm64-l4tm',
                    'boot/vmlinuz-4.3.0-3-arm64-l4tm',
                    'etc/hosts',
                    'etc/hostname',
                    'etc/apt/sources.list']

        for fs_dirname in fs_dirtree:
            os.makedirs('%s/%s' % (cls.fs_img, fs_dirname))

        for fs_file in fs_files:
            file_path = '%s/%s' % (cls.fs_img, fs_file)
            with open(file_path, 'a') as file_obj:
                os.utime(file_path, None)


    @classmethod
    def tearDown(cls):
        if os.path.isdir(cls.tmp_folder):
            rmtree(cls.tmp_folder)

    def test_cleanout_kernel(self):
        """
            Assume there is a mock filesystem image already created. Thus, try
        to move boot/ files into tmp directory using customize_node.cleanout_kernel
        function.
        """
        CN.cleanout_kernel(self.fs_img, self.tmp_folder)
        boot_files = ['initrd.img-4.3.0-3-arm64-l4tm',
                      'vmlinuz-4.3.0-3-arm64-l4tm']
        for boot_file in boot_files:
            boot_old = '%s/boot/%s' % (self.fs_img, boot_file)
            boot_new = '%s/%s' % (self.tmp_folder, boot_file)
            self.assertFalse(os.path.exists(boot_old),
                    '"%s" should have been removed!' % (boot_old))
            self.assertTrue(os.path.exists(boot_new),
                            '"%s" was not found!' % (boot_new))



if __name__ == '__main__':
    unittest.main()
