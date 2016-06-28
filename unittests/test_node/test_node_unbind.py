#!/usr/bin/python3 -tt
"""
    Test fix_init function of customize_node.py script.
"""
import json
import unittest
import tmcmd

import config
from tm_librarian.tmconfig import TMConfig
from pdb import set_trace

class UnbindNodeTest(unittest.TestCase):

    tm_cmd = None
    tmconfig = None
    node = None
    manifest_for_test = None

    @classmethod
    def setUp(cls):
        """
        """
        set_trace()
        cls.tm_cmd = tmcmd.tmnode
        cls.tmconfig = TMConfig(config.TMCONFIG)
        cls.node = cls.tmconfig.nodes[1].coordinate
        manifest_for_test = os.path.dirname(__file__) + '/manifest.test'
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


    def test_node_delete(self):
        """
            Test the return code of the existed node.
        First: upload a Test manifest to a server.
        Second: assign a Manifest to a Node
        Third: check if binding is correct
        """
        expected_code = 204

        output = self.tm_cmd.set_node([self.node, ----------------------])

        output = self.tm_cmd.delete(self.node])
        self.assertTrue(False, 'Not Implemented')


if __name__ == '__main__':
    unittest.main()
