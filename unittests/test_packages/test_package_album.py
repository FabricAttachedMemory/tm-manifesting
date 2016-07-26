#!/usr/bin/python3
"""
    Set of tests for for tmcmd/tm_package.py of the API.
"""
import json
import os
import unittest
from pdb import set_trace

from tmms.tm_cmd import tmcmd
from tmms.unittests import suite_config as config


class PackageTest(unittest.TestCase):

    URL = ''
    tm_cmd = None
    pkg_name = 'album'
    mock_file = os.path.dirname(os.path.realpath(__file__)) + '/mock-data/album.package.json'

    @classmethod
    def setUpClass(cls):
        cls.URL = config.MANIFESTING_SERVER
        cls.tm_cmd = tmcmd.tmpkg



    def test_album_isInList(self):
        """ Test if showpkg can return non-error data for the package. """
        output = self.tm_cmd.listall()
        output = json.loads(output)
        self.assertTrue('200' in output,
                        '%s is not 200. Incorrect status returned.' % output.keys())


    def test_album_exists(self):
        """ Test if showpkg can return non-error data for the package. """
        output = self.tm_cmd.show(self.pkg_name)
        output = json.loads(output)
        self.assertTrue('200' in output,
                        '%s is not 200. Incorrect status returned.' % output.keys())


    def test_pkg_not_exists(self):
        """ Test if showpkg will return error message for non-existed package. """
        output = self.tm_cmd.show('album1')
        output = json.loads(output)
        self.assertTrue('404' in output,
                        '%s is not 404. Incorrect status returned for missing pkg.' % output.keys())


if __name__ == '__main__':
    unittest.main()
