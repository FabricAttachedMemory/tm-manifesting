#!/usr/bin/python3
"""
    Set of tests for for tmcmd/tm_package.py of the API.
"""
import json
import os
import unittest
from pdb import set_trace

from tmms.tm_cmd import tmcmd
from tmms import manifest_api


class PackageTest(unittest.TestCase):


    @classmethod
    def setUpClass(cls):
        cls.app = manifest_api.create_app()
        manifest_api.register_blueprints(cls.app)
        cls.app.testing = True
        cls.client = cls.app.test_client()
        cls.base_endpoint = '/manifesting/api/'


    def test_return_all(self):
        """ Status for returning all packages in the repo """
        response = self.client.get(self.base_endpoint + 'packages/')
        self.assertTrue(response.status_code == 200,
                        '%s is not 200 for returring all packages list!' %\
                        response.status_code)


    def test_album_isInList(self):
        """ Test if showpkg can return non-error data for the package. """
        response = self.client.get(self.base_endpoint + 'package/album')
        self.assertTrue(response.status_code == 200,
                        '%s is not 200. Incorrect status returned.' %\
                        response.status_code)


    def test_manifesting_inList(self):
        """ Need to test OTHER_MIRRORS capailities. tm-manifesting should typically
        come from OTHER_MIRRORS, so check if it is in the list of all packages.
        NOTE: This might not be true at some point.
        """
        response = self.client.get(self.base_endpoint + 'package/tm-manifesting')
        self.assertTrue(response.status_code == 200)


    def test_pkg_not_exists(self):
        """ Test if showpkg will return error message for non-existed package. """
        response = self.client.get(self.base_endpoint + 'package/PlanetExpress')
        self.assertTrue(response.status_code == 404,
                        '%s is not 404. Incorrect status returned for missing pkg.' % \
                        response.status_code)


if __name__ == '__main__':
    unittest.main()
