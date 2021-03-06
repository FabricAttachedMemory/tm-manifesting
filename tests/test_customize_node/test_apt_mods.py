#!/usr/bin/python3 -tt
"""
    Test cleanup_sources_list function of customize_node.py script.
"""
from pdb import set_trace
from argparse import Namespace
import os
import sys
import unittest
import tempfile
from shutil import rmtree, copytree

import config
from config import CN


class AptModTest(unittest.TestCase):

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

        args = {'new_fs_dir' : self.fs_img,
                'hostname' : 'unittest_hostname',
                'node_coord' : 'unittest_node_coordinate',
                'repo_mirror' : 'unittest/repo/url',
                'repo_release' : 'unittest_release',
                'repo_areas' : ['test_area_1', 'test_area_2'],
                'dryrun' : True}
        args = Namespace(**args)

        CN.cleanup_sources_list(args)

        self.assertFalse(os.path.exists(baselist_file),
                        'base.list file was not removed!')
        self.assertTrue(os.path.exists(sourceslist_file),
                    'What happened to sources.list file? Where is it off to?')
        self.assertFalse(os.path.exists(baselist_file), 'Basefile was not removed.')

        sources_data = None
        with open(sourceslist_file, 'r') as file_obj:
            sources_data = file_obj.read()

        self.assertTrue(args.hostname in sources_data, 'Hostname not in sources.list.')
        self.assertTrue(args.node_coord in sources_data, 'node_coord not in sources.list.')
        self.assertTrue(args.repo_mirror in sources_data, 'Repo mirror not in sources.list.')
        self.assertTrue(args.repo_release in sources_data, 'Repo release not in sources.list.')
        self.assertTrue(' '.join(args.repo_areas) in sources_data, 'Repo areas not in sources.list.')


    def test_set_proxy_all(self):
        """ """
        tmp_file = tempfile.NamedTemporaryFile(dir='/tmp/')
        proxy_url = 'http://some.proxy.com:4848'
        expected = [
            'Acquire::http::Proxy "%s";' % proxy_url,
            'Acquire::https::Proxy "%s";' % proxy_url,
            'Acquire::ftp::Proxy "%s";' % proxy_url,
        ]
        CN.set_apt_proxy(tmp_file.name, proxy_url)

        file_lines = None
        with open(tmp_file.name, 'r') as file_obj:
            file_lines = file_obj.read().split('\n')
        set_trace()
        for expected_line in expected:
            self.assertTrue(expected_line in file_lines,
                        '%s not in modded apt.conf!' % expected_line)


    def test_set_proxy_single(self):
        """ """
        tmp_file = tempfile.NamedTemporaryFile(dir='/tmp/')
        proxy_url = { 'http' : 'http://some.proxy.com:4848' }
        expected = 'Acquire::http::Proxy "%s";' % proxy_url['http']

        CN.set_apt_proxy(tmp_file.name, proxy_url)

        file_lines = None
        with open(tmp_file.name, 'r') as file_obj:
            file_lines = file_obj.read().split('\n')

        file_lines = [ line for line in file_lines if line ]

        self.assertTrue(len(file_lines) == 1, 'Should be just one line')
        self.assertTrue(expected in file_lines,
                    '%s not in modded apt.conf!' % expected)

if __name__ == '__main__':
    unittest.main()
