#!/usr/bin/python3
"""
    Set of tests for /tm-manifest/tmcmd/ module.
"""

import unittest


class PackageTest(unittest.TestCase):

    def test_import(self):
        """ Check if tmcmd module can be imported """
        status = True
        try:
            import tmcmd
            status = True
        except ImportError:
            status = False

        self.assertTrue(status, 'Could not import module! ImportError.')


    def test_tmpkg_exists(self):
        """
            Check if tmpkg variable of type TmPackage is created successfully by
        __init__.py script for tmcmd module.
        """
        import tmcmd
        status = True
        try:
            tmcmd.tmpkg
            status = True
        except AttributeError:
            status = False
        self.assertTrue(status, 'tmcmd.tmpkg was not initialized correctly! AttributeError.')

        self.assertIsNotNone(tmcmd.tmpkg, 'tmcmd.tmpkg is created, but is None! Not good.')


if __name__ == '__main__':
    unittest.main()
