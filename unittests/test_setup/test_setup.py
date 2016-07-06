#!/usr/bin/python3 -tt
"""
    Test tm_utils.environment.ratify() script.
"""
import os
import unittest
from shutil import rmtree

import setup
from pdb import set_trace


class EnvironmentScriptTest(unittest.TestCase):

    tmp = '/tmp/tm_setup_unittest/'
    mock_hook = os.path.realpath('mock-data/mock_test.pth')
    mock_path = None
    python_dist = '/usr/local/lib/python3.4/dist-packages/'
    python_hooked = None


    @classmethod
    def setUp(cls):
        """
            Prepare testing environment for the unittest to use.
        """
        if os.path.exists(cls.tmp):
            rmtree(cls.tmp)
        os.mkdir(cls.tmp)
        cls.mock_path = os.path.realpath(__file__)
        cls.mock_path = os.path.dirname(cls.mock_path)
        cls.python_hooked = cls.python_dist + '/' + os.path.basename(cls.mock_hook)

        with open(cls.mock_hook, 'w') as file_obj:
            file_obj.write(cls.mock_path)


    @classmethod
    def tearDown(cls):
        """ Clean up test environment. """
        if os.path.exists(cls.tmp):
            rmtree(cls.tmp)
        if cls.python_hooked is not None:
            if os.path.exists(cls.python_hooked):
                os.remove(cls.python_hooked)


    def test_python_path(self):
        """
            Test if setup imports correct python path into environment.
        """
        setup.set_python_path(self.mock_hook, self.python_dist)

        self.assertTrue(os.path.exists(self.python_hooked))


    def test_python_path_overwrite(self):
        """
            Test if can overwrite exiting .pth file and check if its contents is
        correct.
        """
        setup.set_python_path(self.mock_hook, self.python_dist)

        self.assertTrue(os.path.exists(self.python_hooked))

        new_path = '/tmp/'
        with open(self.mock_hook, 'w') as file_obj:
            file_obj.write(new_path)

        self.assertTrue(os.path.exists(self.python_hooked))

        with open(self.python_hooked, 'r') as file_obj:
            file_data = file_obj.read().split('\n')

        self.assertTrue(new_path in file_data)
        self.assertTrue(self.mock_path not in file_data)


if __name__ == '__main__':
    unittest.main()
