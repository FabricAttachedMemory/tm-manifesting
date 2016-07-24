#!/usr/bin/python3 -tt
"""
    Test utils/utils.py script.
"""
import os
import tempfile
import unittest
from shutil import rmtree

from tmms.utils import utils
from pdb import set_trace


class EnvironmentScriptTest(unittest.TestCase):

    #tmp = '/tmp/tm_utils_unittest/'
    tmp = None

    @classmethod
    def setUp(cls):
        """
            Prepare testing environment for the unittest to use.
        """
        cls.tmp = str(tempfile.mkdtemp())


    def tearDown(cls):
        """ Clean up test environment. """
        if os.path.exists(cls.tmp):
            rmtree(cls.tmp)


    def test_ratify_nonlist_exists(self):
        """
            Pass path as a string to test 'singular' path validation of files
        and dirs. Returned output must be empty list.
        """
        junk_dir = self.tmp + '/junk'
        junk_file = self.tmp + '/junk.file'
        with open(junk_file, 'w') as file_obj:
            file_obj.write('testing')

        os.mkdir(junk_dir)

        output = utils.ratify(junk_dir)
        self.assertTrue(not output)

        output = utils.ratify(junk_file)
        self.assertTrue(not output)



    def test_ratify_list_exists(self):
        """
            Path list of files and dirs path to validate. If returned list is
        not empty - then something is wrong.
        """
        junk_dir = self.tmp + '/junk'
        junk_file = self.tmp + '/junk.file'
        with open(junk_file, 'w') as file_obj:
            file_obj.write('testing')

        os.mkdir(junk_dir)

        output = utils.ratify([junk_dir, junk_file])
        self.assertTrue(not output)



    def test_ratify_nonlist_notexists(self):
        """
            Path singular dir path and file path that doesn't exist. Both file
        and dir must be in the returned list. If not - something is wrong.
        """
        junk_dir = self.tmp + '/junk'
        junk_file = self.tmp + '/junk.file'

        output = utils.ratify(junk_dir)
        self.assertTrue(junk_dir in output)

        output = utils.ratify(junk_file)
        self.assertTrue(junk_file in output)



    def test_ratify_list_notexists(self):
        """
            Path list of file and dir path that doesn't exist. Both file
        and dir must be in the returned list. If not - something is wrong.
        """
        junk_dir = self.tmp + '/junk'
        junk_file = self.tmp + '/junk.file'

        output = utils.ratify([junk_dir, junk_file])
        self.assertTrue(junk_dir in output)
        self.assertTrue(junk_file in output)


if __name__ == '__main__':
    unittest.main()
