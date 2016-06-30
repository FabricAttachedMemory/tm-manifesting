#!/usr/bin/python3 -tt
"""
    Test fix_init function of customize_node.py script.
"""
import json
import unittest
import tmcmd as TMCMD

import suite_config as config
from pdb import set_trace

class BindNodeTest(unittest.TestCase):

    tmcmd = None
    tmconfig = None
    coords = []
    manifest = 'testing'
    manifest_file = './mock-data/manifest.test'

    @classmethod
    def setUp(cls):
        """
        """
        cls.tmcmd = TMCMD.tmnode
        cls.tmconfig = config.hpetmconfig
        cls.coords = sorted([node.coordinate for node in cls.tmconfig.nodes])

        TMCMD.tmmanifest.upload([cls.manifest_file])



    @classmethod
    def tearDown(cls):
        return None


    def testNodeList(self):
        """
            Test api to list nodes information. Output must comply with ERS.
        """
        output = json.loads(self.tmcmd.listall())

        self.assertTrue('nodes' in output,
                        'listall does not comply with ERS. No "nodes" key.')

        self.assertTrue(sorted(self.coords) == sorted(output['nodes']),
                        'listall does not comply with ERS. Not all coords match tmconfig.')


    def testNodeListStatus(self):
        """
            Test api list all nodes return correct status code.
        """
        output = json.loads(self.tmcmd.listall())
        self.assertTrue('200' in output,
                        'listall return status code does not comply with ERS.')

    def testShowNodeStatus(self):
        """
        """
        output = json.loads(TMCMD.tmmanifest.upload([]))

        args = [self.coords[1], ]
        output = self.tmcmd.set_node()

        output = json.loads(self.tmcmd.show([self.coords[1]])


    def testShowNodeExist(self):
        """
            Test api abbility to get a specifiec node status.
        """
        output = json.loads(self.tmcmd.show([cls.coords[1]))
        fields_check = self.node_status_fiels(output)

        self.assertTrue(fields_check,
                        'Node status does not comply with ERS. Not all fields presented.')


    def node_status_fields(self, response):
        """
        """
        if 'mappings' not in response:
            return False

        fields = ['mafniest', 'status', 'message']
        for expected in fields:
            if expected not in response:
                return False
        return True


if __name__ == '__main__':
    unittest.main()
