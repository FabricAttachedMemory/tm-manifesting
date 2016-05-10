#!/usr/bin/python3
"""
    Set of tests for for tmcmd/tm_package.py of the API.
"""
import unittest
import tmcmd
import json
from pdb import set_trace
import config

class PackageTest(unittest.TestCase):

    URL = ''
    tm_cmd = None
    pkg_name = 'album'

    @classmethod
    def setUpClass(cls):
        cls.URL = config.MANIFESTING_SERVER
        cls.tm_cmd = tmcmd.tmpkg


    def test_album_isInList(self):
        """ Test if showpkg can return non-error data for the package. """
        output = self.tm_cmd.listall()
        status = '"%s"' % (self.pkg_name) in output
        self.assertTrue(status, msg='"album" package should be in the list')


    def test_album_exists(self):
        """ Test if showpkg can return non-error data for the package. """
        output = self.tm_cmd.show(self.pkg_name)
        status = 'error' in output
        self.assertFalse(status, msg='"album" package should be in the list')


    def test_album_exists(self):
        """ Test if showpkg can return non-error data for the package. """
        output = self.tm_cmd.show(self.pkg_name)
        status = 'error' in output
        self.assertFalse(status, msg='"album" package should be in the list')


    def test_pkg_not_exists(self):
        """ Test if showpkg will return error message for non-existed package. """
        output = self.tm_cmd.show('album1')
        status = 'error' in output
        self.assertTrue(status,
                msg='"album1" package should not be in the list')


    def test_album_content(self):
        """ Test if showpkg can return correct data for the package. """
        output = self.tm_cmd.show(self.pkg_name)
        expected = None
        with open('./mock-data/album.package.json', 'r+') as file_obj:
            expected = file_obj.read()

        status = output in expected
        self.assertTrue(status,
                msg='Expected data in mock-data/album.json does not match\
                with produced output.')


if __name__ == '__main__':
    unittest.main()
