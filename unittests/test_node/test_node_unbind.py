#!/usr/bin/python3 -tt
"""
    Test fix_init function of customize_node.py script.
"""
import json
import unittest
import tmcmd

import config
from pdb import set_trace

class UnbindNodeTest(unittest.TestCase):

    tm_cmd = None

    @classmethod
    def setUp(cls):
        """
        """
        cls.tm_cmd = tmcmd.tmnode
        return None


    @classmethod
    def tearDown(cls):
        return None


    def test_node_not_found(self):
        """
            Test the return code of the non-existed node. Must return 404.
        """
        expected_code = '404'
        output = self.tm_cmd.delete(['testing/node/path/1'])
        output = json.loads(output)
        self.assertTrue(expected_code in output, '404 status code was not returned.')


    def test_node_found(self):
        """
            Test the return code of the existed node.
        First: upload a Test manifest to a server.
        Second: assign a Manifest to a Node
        Third: check if binding is correct
        """
        self.assertTrue(False, 'Not Implemented')


if __name__ == '__main__':
    unittest.main()
