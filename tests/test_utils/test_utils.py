#!/usr/bin/python3 -tt
"""
    Test customize_node.py script.
"""
from pdb import set_trace

import os
import tempfile
import unittest
from shutil import rmtree, copytree

import tmms.utils.utils as TmmsUtils


class UtilsTest(unittest.TestCase):

    tmp_folder = None

    @classmethod
    def setUp(cls):
        cls.tmp_folder = tempfile.mkdtemp()
        if os.path.isdir(cls.tmp_folder):
            rmtree(cls.tmp_folder)
        os.makedirs(cls.tmp_folder)


    @classmethod
    def tearDown(cls):
        if os.path.isdir(cls.tmp_folder):
            rmtree(cls.tmp_folder)


    def test_compress(self):
        """ Test directory compression utils """
        test_dir = '%s/to_compress/' % self.tmp_folder
        test_file_name = 'test_copy_orig'
        test_file = '%s/%s' % (test_dir, test_file_name)
        compressed_dir = '%s/compressed.tar' % self.tmp_folder
        uncompressed_dir = '%s/uncompressed' % self.tmp_folder

        self.touch_folder(test_dir)
        self.touch_folder(uncompressed_dir)
        self.touch_file(test_file)

        TmmsUtils.make_tar(compressed_dir, test_dir)

        self.assertTrue(os.path.exists(compressed_dir),
                        '%s was not compressed into %s!' % (test_dir, compressed_dir))

        TmmsUtils.untar(uncompressed_dir, compressed_dir)
        self.assertTrue(os.path.exists(uncompressed_dir + '/' + test_file_name))


    def test_deb_components_valid(self):
        '''
            Validate sources.list url can be parsed properly by checking
            url, release and areas values match between origin and parsed.
        '''
        url = 'http://some.deb.mirror/debian/'
        release = 'jessie'
        areas = 'main contrib'
        full_source = 'deb {url} {release} {areas}'\
                    .format(url=url, release=release, areas=areas)
        pieces = TmmsUtils.deb_components(full_source)

        self.assertTrue(url == pieces.url)
        self.assertTrue(release == pieces.release)
        self.assertTrue(areas.split(' ') == pieces.areas)


    def test_deb_components_invalid(self):
        ''' '''
        url = 'http://some.deb.mirror/debian/'
        release = 'jessie'
        areas = 'main contrib'
        full_source = '{url} {release} {areas}'\
                    .format(url=url, release=release, areas=areas)
        pieces = TmmsUtils.deb_components(full_source)

        self.assertFalse(pieces.url)
        self.assertFalse(pieces.release)
        self.assertFalse(pieces.areas)


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
