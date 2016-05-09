#!/usr/bin/python3 -tt
"""
    Test cleanup_sources_list function of customize_node.py script.
"""
from pdb import set_trace

import os
import sys
import unittest
from shutil import rmtree, copytree

import config
from config import CN


class CleanupSourcesListTest(unittest.TestCase):

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


    def test_cleanup_sources_list(self):
        """
            Assume there is a mock filesystem image already created. Thus, try
        fix sources.list and sources.list.d/base.list using customize_node.cleanup_sources_list
        function, e.g. move content of base.list into sources.list and removing base.list file.
        """
        sourceslist_file = '%s/etc/apt/sources.list' % self.fs_img
        baselist_file = '%s/etc/apt/sources.list.d/base.list' % self.fs_img
        CN.cleanup_sources_list(self.fs_img)

        self.assertFalse(os.path.exists(baselist_file),
                        'base.list file was not removed!')
        self.assertTrue(os.path.exists(sourceslist_file),
                    'What happened to sources.list file? Where is it off to?')
        self.assertIsNone(CN.cleanup_sources_list(self.fs_img), 'base.list still exists?')


    #TODO: test excepionts!

if __name__ == '__main__':
    unittest.main()
