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

    #TODO: TEST utils functions


if __name__ == '__main__':
    unittest.main()
