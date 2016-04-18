#!/usr/bin/python3
"""
    Set of tests for for tmcmd/tm_package.py of the API.
"""

import unittest
import tmcmd


class PackageTest(unittest.TestCase):

    URL = 'http://zachv.americas.hpqcorp.net:31178/manifesting/api/'
    tm_cmd = None
    pkg_name = '0ad-data'

    @classmethod
    def setUpClass(cls):
        cls.tm_cmd = tmcmd.tmpkg


    def test_0ad_data_exists(self):
        """ Test if showpkg can return non-error data for the package. """
        output = self.tm_cmd.showpkg(self.pkg_name)
        status = 'error' in output
        self.assertFalse(status, msg='"0ad-data" package should be in the list')


    def test_0ad_data_exists(self):
        """ Test if showpkg can return non-error data for the package. """
        output = self.tm_cmd.showpkg(self.pkg_name)
        status = 'error' in output
        self.assertFalse(status, msg='"0ad-data" package should be in the list')


    def test_pkg_not_exists(self):
        """ Test if showpkg will return error message for non-existed package. """
        output = self.tm_cmd.showpkg('soup-no-soup')
        status = 'error' in output
        self.assertTrue(status,
                msg='"soup-no-soup" package should not be in the list')


    def test_0ad_data_content(self):
        """ Test if showpkg can return correct data for the package. """
        output = self.tm_cmd.showpkg(self.pkg_name)
        expected = None
        with open('./mock-data/0ad-data.package.json', 'r+') as file_obj:
            expected = file_obj.read()
        self.assertEqual(output, expected,
                msg='Expected data in mock-data/0ad-data.json does not match\
                with produced output.')


if __name__ == '__main__':
    unittest.main()
