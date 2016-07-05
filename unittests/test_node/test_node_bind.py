#!/usr/bin/python3 -tt
"""
    Test fix_init function of customize_node.py script.
"""
import json
import unittest
import time
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

        TMCMD.tmmanifest.upload(['', cls.manifest_file])



    @classmethod
    def tearDown(cls):
        TMCMD.tmmanifest.delete([cls.manifest])
        status = cls.tmcmd.show([cls.coords[1]])
        if '200' not in status:
            cls.tmcmd.delete([cls.coords[1]])


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

    '''
    def testSetNodeAndStatus(self):
        """
        """
        args = [self.manifest, self.coords[1]]
        output = json.loads( self.tmcmd.set_node(args) )
        self.assertTrue('201' in output, 'WOW! Node was overwritten. Not good.')
        time.sleep(1)

        status = json.loads( self.tmcmd.show([self.coords[1]]) )
        self.assertTrue(self.node_status_fields(status), 'Node status while building does not comply.')
        self.assertTrue(status['status'] == 'building', 'Node is not building??')

        while status['status'] == 'building':
            status = json.loads( self.tmcmd.show([self.coords[1]]) )
            self.assertTrue(self.node_status_fields(status), 'Node status while building does not comply.')
            time.sleep(3)

        self.assertTrue(status['status'] == 'done', 'Node is not done?')
    '''

# =================================================================

    def node_status_fields(self, response):
        """
        """
        fields = ['manifest', 'status', 'message']
        for expected in fields:
            if expected not in response:
                return False
        return True


if __name__ == '__main__':
    unittest.main()
