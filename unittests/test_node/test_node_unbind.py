#!/usr/bin/python3 -tt
"""
    Test fix_init function of customize_node.py script.
"""
import os
import json
import shutil
import unittest

import config
import tmcmd
from tm_librarian.tmconfig import TMConfig
from pdb import set_trace

class UnbindNodeTest(unittest.TestCase):

    tm_cmd = None
    tmconfig = None
    node = None
    manifest = None
    manifest_tftp = None
    cpio_path = None

    @classmethod
    def setUp(cls):
        """
        """
        cls.manifest = os.path.dirname(__file__) + '/manifest.test'

        cls.tm_cmd = tmcmd.tmnode
        cls.tmconfig = TMConfig(config.TMCONFIG)
        cls.node = cls.tmconfig.nodes[1].coordinate
        cls.manifest_tftp = config.IMAGES + '/node02/' + os.path.basename(cls.manifest)
        set_trace()
        shutil.copyfile(cls.manifest, cls.manifest_tftp)
        return None


    @classmethod
    def tearDown(cls):
        tmcmd.tmmanifest.delete(['manifest.test'])
        if os.path.exists(cls.manifest_for_test_path):
            os.remove(cls.manifest_for_test_path)

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
            Test the return code of the existed node. First: upload a Test manifest
        to a server. Second: assign a Manifest to a Node. Third: check if binding 
        is correct
        """
        expected_code = 204

        #output = self.tm_cmd.set_node([self.node, self.manifest_for_test])

        #output = self.tm_cmd.delete(self.node])
        self.assertTrue(False, 'Not Implemented')


if __name__ == '__main__':
    unittest.main()
