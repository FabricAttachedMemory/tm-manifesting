#!/usr/bin/python3 -tt
"""
"""
from pdb import set_trace

import glob
import json
import os
import sys
import tempfile
import unittest
from shutil import rmtree, copytree

import suite_config as config
from pdb import set_trace

MANIFEST_UPLOADS = config.server_config['MANIFEST_UPLOADS']

class ManifestTest(unittest.TestCase):

    tmcmd = None
    backup_folder = None
    prefix_types = ['', 'unittest', 'unittest/mock']
    mock_file = os.path.dirname(os.path.realpath(__file__)) + '/mock-data/manifest.test'
    manifest = None

    @classmethod
    def setUp(cls):
        cls.backup_folder = tempfile.mkdtemp()
        cls.tmcmd = config.tmcmd.tmmanifest
        if cls.manifest is None:
            with open(cls.mock_file, 'r') as file_obj:
                cls.manifest = json.loads(file_obj.read())


    @classmethod
    def tearDown(cls):
        for prefix in cls.prefix_types:
            tested_manifest = prefix + '/' + cls.manifest['name']
            tested_manifest = os.path.normpath(tested_manifest).strip('/')
            uploaded = cls.tmcmd.show([tested_manifest])
            uploaded = json.loads(uploaded)
            if '404' not in uploaded:
                cls.tmcmd.delete(prefix + '/' + tested_manifest)


    def testUploadNoPrefix(self):
        """
            Test upload and delete of the manifest from mock-data/ without Prefix
        """
        output = self.tmcmd.upload(['', self.mock_file])
        output = json.loads(output)
        self.assertTrue('201' in output,
                        '%s is not 201. New manifest upload.' % output.keys())

        uploaded = self.tmcmd.show([self.manifest['name']])
        uploaded = json.loads(uploaded)
        self.assertTrue('200' in uploaded,
                        '%s is not 200. Manifest overwrite.' % output.keys())

        deleted = self.tmcmd.delete(self.manifest['name'])
        deleted = json.loads(deleted)
        self.assertTrue('204' in deleted,
                        '%s is not 204. Manifest delete status code.' % output.keys())

        uploaded = self.tmcmd.show(self.manifest['name'])
        uploaded = json.loads(uploaded)
        self.assertTrue('404' in uploaded, 'Uploaded manifest was not deleted?')


    def testUploadPrefix(self):
        """
            Test upload and delete of the manifest from mock-data/ with Prefix
        """
        self.tmcmd.upload([self.prefix_types[1], self.mock_file])
        self.tmcmd.upload([self.prefix_types[2], self.mock_file])

        for prefix in self.prefix_types[1:]:
            tested_manifest = prefix + '/' + self.manifest['name']
            tested_manifest = tested_manifest.strip('/')
            uploaded = self.tmcmd.show([tested_manifest])
            uploaded = json.loads(uploaded)

            self.assertTrue('200' in uploaded, 'Manifest was not uploaded??')

            self.assertTrue(uploaded['200']['name'] == self.manifest['name'], 'Manifest name didnt match.')
            deleted = self.tmcmd.delete([tested_manifest])
            deleted = json.loads(deleted)
            self.assertTrue('204' in deleted,
                            '%s is not 204. Manifest delete status code.' % deleted.keys())

            uploaded = self.tmcmd.show(tested_manifest)
            uploaded = json.loads(uploaded)

            self.assertTrue('404' in uploaded, 'Uploaded manifest was not deleted?')


    def testUploadStatusCode(self):
        """
        """
        uploaded = self.tmcmd.upload([self.prefix_types[0], self.mock_file])
        self.assertTrue('201' in uploaded, 'Incorrect status code for freash manifest upload.')

        uploaded = self.tmcmd.upload([self.prefix_types[0], self.mock_file])
        self.assertTrue('200' in uploaded, 'Incorrect status code for manifest overwrite upload.')

        uploaded = self.tmcmd.delete([self.manifest['name']])
        self.assertTrue('204' in uploaded, 'Incorrect status code for manifest delete.')

        uploaded = self.tmcmd.delete([self.manifest['name']])
        self.assertTrue('404' in uploaded, 'Incorrect status code for manifest delete.')



if __name__ == '__main__':
    unittest.main()
