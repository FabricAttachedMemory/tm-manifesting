#!/usr/bin/python3 -tt
"""
    Test fix_init function of customize_node.py script.
"""
import json
import os
import unittest
import time

from pdb import set_trace

from tmms.tm_cmd import tmcmd as TMCMD
from tmms.tests import suite_config as config
from tm_librarian.tmconfig import TMConfig


class BindNodeTest(unittest.TestCase):

    tmcmd = None
    tmconfig = None
    coords = []
    manifest = 'testing'
    manifest_file = os.path.dirname(os.path.realpath(__file__)) + '/mock-data/manifest.test'

    @classmethod
    def setUp(cls):
        """
        """
        cls.tmcmd = TMCMD.tmnode
        cls.tmconfig = TMConfig('/etc/tmconfig')    # FIXME: observe /etc/tmms
        try:
            cls.coords = list(  # ordered by node_id
                [node.coordinate for node in cls.tmconfig.allNodes])
        except Exception:
            cls.coords = sorted([node.coordinate for node in cls.tmconfig.allNodes])


        TMCMD.tmmanifest.upload(['', cls.manifest_file])
        output = cls.tmcmd.show([cls.coords[1]])
        if '204' not in output:
            cls.tmcmd.delete([cls.coords[1]])


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

        self.assertTrue('200' in output,
                    'listing all nodes status code is not 200: %s instead.' % output.keys())

        self.assertTrue('nodes' in output['200'],
                        'listall does not comply with ERS. No "nodes" key.')

        self.assertTrue(set(self.coords) == set(output['200']['nodes']),
                        'listall does not comply with ERS. Not all coords match tmconfig.')


    def testNodeListStatus(self):
        """
            Test api list all nodes return correct status code.
        """
        output = json.loads(self.tmcmd.listall())
        self.assertTrue('200' in output,
                        'listall return status code does not comply with ERS.')
        self.assertTrue('nodes' in output['200'],
                        'listall output does not comply with ERS. Missing "nodes" field.')


    def testSetNodeAndStatus(self):
        """
        """
        node = self.coords[-1]
        args = [node, self.manifest]

        output = json.loads(self.tmcmd.delete([node, ]))    # Cleaning up node before test
        self.assertTrue('204' in output,
            'Expected 204 after unsetnode: %s instead' % output)

        output = json.loads(self.tmcmd.set_node(args))
        self.assertTrue('201' in output or '200' in output,
            'Neither 200 nor 201 was returned on setnode: %s instead' % output)

        time.sleep(5)

        output = json.loads(self.tmcmd.delete([node,]))
        self.assertTrue('409' in output,
                    'Deleting node while building status incorrect [%s]' % output)

        status = json.loads(self.tmcmd.show([node, ]))

        self.assertTrue('200' in status,
            'Status not 200 while building: %s' % status.keys())

        status = status['200']

        self.assertTrue(self.node_status_fields(status),
            'Illegal status while building image: %s' % status['status'])

        # Don't know why interpolation doesn't work in-situ.
        msg = '%s: expected status "building", got "%s" (%s)' % (
            node, status['status'], status['message'])

        # This test can fail if the server is run --debug; don't do dat!
        self.assertTrue(status['status'] == 'building', msg)

        while status['status'] == 'building':
            status = json.loads(self.tmcmd.show([node, ]))
            self.assertTrue('200' in status,
                'Status not 200 while building: %s' % status.keys())
            status = status['200']

            self.assertTrue(self.node_status_fields(status),
                'Illegal status while building: %s' % status['status'])
            time.sleep(10)

        msg = '%s: expected status == ready, got %s' % (node, str(status))
        self.assertTrue(status['status'] == 'ready', msg)

        deleted = json.loads(self.tmcmd.delete([node, ]))
        self.assertTrue('204' in deleted,
            '204 was not returned after node delete: %s' % deleted)

        status = json.loads(self.tmcmd.show([node, ]))
        self.assertTrue('204' in status,
                        '204 for non binded node was not returned: %s' % status.keys())

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
