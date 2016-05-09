#!/usr/bin/python3 -tt
"""
    Test customize_node.py script.
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



class PackageTest(unittest.TestCase):

    tmp_folder = "/tmp/UNITTEST_CUSTOMNODE/"

    @classmethod
    def setUp(cls):
        if os.path.isdir(cls.tmp_folder):
            rmtree(cls.tmp_folder)
        os.makedirs(cls.tmp_folder)


    @classmethod
    def tearDown(cls):
        if os.path.isdir(cls.tmp_folder):
            rmtree(cls.tmp_folder)


    def test_copy_target_into_file(self):
        """
            Create an empty file inside tmp folder and copy into the
        same folder.
        """
        test_file = '%s/test_copy.orig' % self.tmp_folder
        test_file_new = '%s.new' % (test_file)
        self.touch_file(test_file)

        CN.copy_target_into(test_file, test_file_new)

        self.assertTrue(os.path.exists(test_file_new),
            'File "%s" was not copied into "%s"!' % (test_file, test_file_new))


    def test_copy_target_into_dir(self):
        """
            Create an empty file inside tmp folder and copy into the
        same folder.
        """
        test_dir = '%s/test_copy_dir.orig/' % self.tmp_folder
        test_dir_new = '%s.new' % (test_dir)
        self.touch_folder(test_dir)

        CN.copy_target_into(test_dir, test_dir_new)

        self.assertTrue(os.path.isdir(test_dir_new),
            'File "%s" was not copied into "%s"!' % (test_dir, test_dir_new))


    def test_remove_target_file(self):
        """
            Touch a test file inside the test directorty(self.tmp_folder) and
        try to remove it using customize_node.remove_target function.
        """
        test_file = '%s/test_remove_file.orig' % self.tmp_folder
        self.touch_file(test_file)

        CN.remove_target(test_file)
        self.assertFalse(os.path.exists(test_file), 'Target "%s" was not removed!' % test_file)


    def test_remove_target_dir(self):
        """
            Touch a test file inside the test directorty(self.tmp_folder) and
        try to remove it using customize_node.remove_target function.
        """
        test_dir = '%s/test_remove_dir.orig/' % self.tmp_folder
        self.touch_folder(test_dir)

        CN.remove_target(test_dir)
        self.assertFalse(os.path.exists(test_dir), 'Target "%s" was not removed!' % test_dir)


    def test_symlink_target(self):
        """
            Touch a test file inside the test directorty(self.tmp_folder) and
        try to create a new symlink inside it folder using customize_node.symlink_target.
        """
        test_file = '%s/test_symlink_file.orig' % self.tmp_folder
        test_file_new = '%s.linked' % test_file
        self.touch_file(test_file)

        CN.symlink_target(test_file, test_file_new)
        self.assertTrue(os.path.exists(test_file_new), 
                'Target "%s" was not linked into "%s"!' % (test_file, test_file_new))


    def test_write_to_file(self):
        """ """
        test_file = '%s/test_wirtefile.orig' % self.tmp_folder
        orig_content = 'Praise the Sun!'
        new_content = 'What is bravery, without a dash of recklessness.'
        with open(test_file, 'w+') as file_obj:
            file_obj.write(orig_content)

        if not os.path.exists(test_file):
            self.assertFalse(True,
                'Couldn\'t create a test file "%s"!' % test_file)

        CN.write_to_file(test_file, new_content)

        file_content = ''
        with open(test_file, 'r') as file_obj:
            file_content = file_obj.read()

        self.assertFalse(orig_content in file_content,
                'File "%s" was not overweritten! Missing original data!' % test_file)
        self.assertTrue(new_content in file_content,
                'File "%s" was not updated with a new data!' % test_file)


    def touch_file(self, filename):
        """ Touch a file that will be used for testing. """
        with open(filename, 'a'):
            os.utime(filename, None)

        if not os.path.exists(filename):
            self.assertFalse(True,
                'Couldn\'t create a test file "%s"!' % filename)


    def touch_folder(self, foldername):
        """ Create a folder tree that will be used for testing. """
        os.makedirs(foldername)

        if not os.path.isdir(foldername):
            self.assertFalse(True,
                'Couldn\'t create a test directory "%s"!' % foldername)


if __name__ == '__main__':
    unittest.main()
