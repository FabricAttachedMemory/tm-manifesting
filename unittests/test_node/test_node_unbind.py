#!/usr/bin/python3 -tt
"""
    Test fix_init function of customize_node.py script.
This test suite touches the following functions:
    tmcmd.tmmanifest.upload
    tmcmd.tmmanifest.show
    tmcmd.tmmanifest.delete

    tmcmd.tmnode.listall
    tmcmd.tmnode.show
    tmcmd.tmnode.set_node
    tmcmd.tmnode.delete
"""
import time
import json
import unittest
import tmcmd

from pdb import set_trace


class UnbindNodeTest(unittest.TestCase):

    tm_cmd = None
    manname = 'testing'
    man_prefix = 'node-test'

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
        First: upload a Test manifest to a server. Use prefixed manifest.
        Second: assign a Manifest to a Node
        Third: check if binding is correct
        """
        man_full_path = '%s/%s' % (self.man_prefix, self.manname)
        tmcmd.tmmanifest.upload([self.man_prefix, 'mock-data/manifest.test'])
        uploaded_manifest = tmcmd.tmmanifest.show(man_full_path)

        self.assertTrue('404' not in uploaded_manifest)
        uploaded_manifest = json.loads(uploaded_manifest)

        isError = None
        try:
            all_nodes = self.tm_cmd.listall()
            all_nodes = json.loads(all_nodes)
            self.assertTrue('nodes' in all_nodes,
                         'listall failed. "Nodes" field is not in the list')

            node = all_nodes['nodes'][-1]
            self.tm_cmd.set_node([man_full_path, node])
            time.sleep(5)
            status = json.loads(self.tm_cmd.show(node))

            while status['status'] == 'building':
                time.sleep(5)
                status = json.loads(self.tm_cmd.show(node))

            self.assertTrue(status['status'] == 'done',
                            'Node status is not done?')

            deleted = json.loads(self.tm_cmd.delete([node]))
            self.assertTrue('204' in deleted,
                            'Node delete status code is not 204! %s instead' % deleted.keys())
        except AssertionError as err:
            print('Not Good: %s' % err )
            isError = err

        self.assertTrue('name' in uploaded_manifest)
        tmcmd.tmmanifest.delete(man_full_path)

        deleted_manifest = tmcmd.tmmanifest.show(man_full_path)
        self.assertTrue('404' in deleted_manifest)

        if isError is not None:
            self.assertTrue(False, str(isError))


if __name__ == '__main__':
    unittest.main()
