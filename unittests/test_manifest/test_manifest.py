#!/usr/bin/python3 -tt
"""
"""
from pdb import set_trace

import glob
import json
import os
import sys
import unittest
from shutil import rmtree, copytree

import suite_config as config
from pdb import set_trace

MANIFEST_UPLOADS = config.server_config.MANIFESTING_ROOT + '/manifest_uploads/'

class ManifestTest(unittest.TestCase):

    tmcmd = None
    backup_folder = '/tmp/manifest_api_test/'
    prefix_types = ['', 'unittest', 'unittest/mock']
    manifest = None

    @classmethod
    def setUp(cls):
        cls.tmcmd = config.tmcmd.tmmanifest
        if cls.manifest is None:
            with open('./mock-data/manifest.test', 'r') as file_obj:
                cls.manifest = json.loads(file_obj.read())


    @classmethod
    def tearDown(cls):
        for prefix in cls.prefix_types:
            tested_manifest = prefix + '/' + cls.manifest['name']
            tested_manifest = os.path.normpath(tested_manifest).strip('/')
            uploaded = cls.tmcmd.show([tested_manifest])
            uploaded = json.loads(uploaded)
            if uploaded.get('name', False):
                cls.tmcmd.delete(prefix + '/' + tested_manifest)


    def testUploadNoPrefix(self):
        """
            Test upload and delete of the manifest from mock-data/ without Prefix
        """
        self.tmcmd.upload(['', './mock-data/manifest.test'])

        uploaded = self.tmcmd.show([self.manifest['name']])
        uploaded = json.loads(uploaded)

        self.tmcmd.delete(self.manifest['name'])
        self.assertTrue(uploaded['name'] == self.manifest['name'],
                        'Manifest name didnt match.')

        uploaded = self.tmcmd.show(self.manifest['name'])
        uploaded = json.loads(uploaded)
        self.assertTrue('404' in uploaded, 'Uploaded manifest was not deleted?')


    def testUploadPrefix(self):
        """
            Test upload and delete of the manifest from mock-data/ with Prefix
        """
        self.tmcmd.upload([self.prefix_types[1], './mock-data/manifest.test'])
        self.tmcmd.upload([self.prefix_types[2], './mock-data/manifest.test'])

        for prefix in self.prefix_types[1:]:
            tested_manifest = prefix + '/' + self.manifest['name']
            tested_manifest = tested_manifest.strip('/')
            uploaded = self.tmcmd.show([tested_manifest])
            uploaded = json.loads(uploaded)

            self.assertFalse('404' in uploaded, 'Manifest was not uploaded??')

            self.assertTrue(uploaded['name'] == self.manifest['name'], 'Manifest name didnt match.')
            self.tmcmd.delete([tested_manifest])

            uploaded = self.tmcmd.show(tested_manifest)
            uploaded = json.loads(uploaded)

            self.assertTrue('404' in uploaded, 'Uploaded manifest was not deleted?')


    def testUploadStatusCode(self):
        """
        """
        uploaded = self.tmcmd.upload([self.prefix_types[0], './mock-data/manifest.test'])
        self.assertTrue('201' in uploaded, 'Incorrect status code for freash manifest upload.')

        uploaded = self.tmcmd.upload([self.prefix_types[0], './mock-data/manifest.test'])
        self.assertTrue('200' in uploaded, 'Incorrect status code for manifest overwrite upload.')

        uploaded = self.tmcmd.delete([self.manifest['name']])
        self.assertTrue('204' in uploaded, 'Incorrect status code for manifest delete.')

        uploaded = self.tmcmd.delete([self.manifest['name']])
        self.assertTrue('404' in uploaded, 'Incorrect status code for manifest delete.')



if __name__ == '__main__':
    unittest.main()
